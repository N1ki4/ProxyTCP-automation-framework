import os
import re

import paramiko
from paramiko import SSHClient
from scp import SCPClient
from pyats.topology import Device, Testbed

import src


_root = src.__path__[0]
_temp_files_dir = os.path.join(_root, "temp")


class FileUtils:
    """Allows file transfer between testing host and devices."""

    def __init__(self, testbed: Testbed, device: Device):
        self.testbed = testbed
        self.device = device

    @property
    def connection_data(self) -> dict:
        """Device address and credentials."""
        connection = self.device.connections.cli.command
        host = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[3]
        username = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[2]
        key_filename = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[1]
        key = paramiko.RSAKey.from_private_key_file(key_filename)

        return {"host": host, "username": username, "pkey": key}

    def copy_from_device(self, source: str) -> None:
        """Copy file from a device.

        Args:
            source (str): filename on the device to copy
        """
        local_file_name = f"{self.device.name}_{source}"
        full_file_path = os.path.join(_temp_files_dir, local_file_name)
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.connection_data["host"],
                username=self.connection_data["username"],
                password="",
                pkey=self.connection_data["pkey"],
                allow_agent=False,
            )

            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_path=source, local_path=full_file_path)


class DumpCon:
    """Connection context manager with the packet capturing feature."""

    def __init__(self, device: Device):
        self.device = device

    def _kill_process(self, name: str) -> None:
        """Kill active process running on the device.

        Args:
            name (str): name of the process to kill
        """
        self.device.execute("echo -ne '\n'")
        pid = self.device.execute(f"pidof {name}")
        if pid:
            command = f"kill -15 {pid}"
            self.device.execute(command + "&& echo -ne '\n'")

    def _get_default_interface(self) -> str:
        """Get default internet traffic interface."""
        command = "route | grep '^default' | grep -o '[^ ]*$'"
        return self.device.execute(command)

    def start_tshark(
        self, interface: str = None, filters: str = None, capfile: str = None
    ) -> None:
        """Start packet capturing with tshark.

        Args:
            interface (str): capture interface
            filters (str): capture filters
            capfile (str): name of pcap file to save results
        """
        base_command = "tshark"
        params = {
            "-i": interface,
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
