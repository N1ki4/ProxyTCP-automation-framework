"""Module contains user defined classes and functions."""

import os
import socket
import re

from pyats.topology import Device, Testbed
from pyats.utils import secret_strings
from paramiko import SSHClient
from scp import SCPClient


FILE_DIR = os.path.join(os.environ["PROJ_ROOT"], "src", "temp")
# path to temporary files directory: /pyats/project/src/temp


class FileUtils:
    """Allows file transfer between testing host and devices."""

    def __init__(self, testbed: Testbed, device: Device):
        self.testbed = testbed
        self.device = device

    @property
    def connection_data(self) -> dict:
        """Device address and credentials."""
        return {
            "address": str(self.device.connections.cli.ip),
            "username": self.testbed.credentials.default.username,
            "password": secret_strings.to_plaintext(
                self.testbed.credentials.default.password
            ),
        }

    def copy_from_device(self, src: str) -> None:
        """Copy file from a device.

        Args:
            src (str): filename on the device to copy
        """
        local_file_name = f"{self.device.name}_{src}"
        full_file_path = os.path.join(FILE_DIR, local_file_name)
        with SSHClient() as ssh:
            ssh.load_system_host_keys()
            ssh.connect(
                self.connection_data["address"],
                username=self.connection_data["username"],
                password=self.connection_data["password"],
                allow_agent=False,
            )

            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_path=src, local_path=full_file_path)


class DumpCon:
    """Connection context manager with the packet capturing feature."""

    def __init__(self, device: Device):
        self.device = device

    def _kill_process(self, name: str) -> None:
        """Kill active process running on the device.

        Args:
            name (str): name of the process to kill
        """
        pid = self.device.execute(f"pidof {name}")
        if pid:
            command = f"kill -15 {pid}"
            self.device.execute(command + "&& echo -ne '\n'")

    def _get_default_interface(self) -> str:
        """Get default internet traffic interface."""
        command = "route | grep '^default' | grep -o '[^ ]*$'"
        return self.device.execute(command)

    def start_tshark(self, filters: str = None, capfile: str = None) -> None:
        """Start packet capturing with tshark.

        Args:
            filters (str): capture filters
            capfile (str): name of pcap file to save results
        """
        base_command = "tshark"
        params = {
            "-i": self._get_default_interface(),
            "-f": f'"{filters}"',
            "-w": capfile,
        }
        background = "-q &"
        command = base_command
        for k, v in params.items():
            if v is not None:
                command += f" {k} {v}"
        command += f" {background}"
        self.device.execute(command)

    def __enter__(self):
        self.device.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._kill_process("tshark")
        self.device.disconnect()


class Curl:
    """Curl.

    Context manager which inplements curl functionality on the remote
    device and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(self, testbed: Testbed, device: Device):
        self.device = device
        self.fileutils = FileUtils(testbed, device)
        self._datafiles = {"curl_file": "curl.txt", "pcap_file": "tshark.pcap"}

    @property
    def datafiles(self) -> dict:
        """Default files to store results."""
        return self._datafiles

    @datafiles.setter
    def datafiles(self, data: dict):
        self._datafiles = data

    @staticmethod
    def get_host_ip(host) -> str:
        """Retrieve IP of the host to set capture filters in tshark."""
        host = re.compile(r"(http|https)://((\w+\.)+\w+)").search(host)[2]
        return socket.gethostbyname(host)

    def send(
        self,
        host: str,
        timeout: int = None,
        proxy_host: str = None,
        proxy_port: str = None,
        write_pcap: bool = False,
    ) -> None:
        """Execute curl command on the device.

        Args:
            host (str): requested hostname
            timeout (int): request timeout
            proxy_host (str): IP of the socks5 proxy server
            proxy_port (str): TCP port of the socks5 proxy server
            write_pcap (bool): start tshark and write pcap
        """

        base_command = f"curl {host}"
        command = base_command
        if proxy_host is not None and proxy_port is not None:
            command += f" --socks5-hostname {proxy_host}:{proxy_port}"
        if timeout is not None:
            command += f" --connect-timeout {timeout}"
        command += f' > {self.datafiles["curl_file"]}'

        with DumpCon(self.device) as con:
            if write_pcap is True:
                ip_filter = self.get_host_ip(host)
                con.start_tshark(
                    filters=f"host {ip_filter}",
                    capfile=self.datafiles["pcap_file"],
                )
            con.device.execute(command + "&& echo -ne '\n'")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.fileutils.copy_from_device(src=self.datafiles["curl_file"])
        self.fileutils.copy_from_device(src=self.datafiles["pcap_file"])


if __name__ == "__main__":

    from pyats.topology import loader

    tb = loader.load("../testbed.yaml")
    dc = tb.devices["user-endpoint-1"]

    with Curl(testbed=tb, device=dc) as curl:

        curl.send(host="https://wiki.archlinux.org/", timeout=5, write_pcap=True)
