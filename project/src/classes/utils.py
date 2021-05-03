import os
import re

import paramiko
from paramiko import SSHClient
from scp import SCPClient
from pyats.topology import Device

import src


_root = src.__path__[0]
_temp_files_dir = os.path.join(_root, "temp")


class FileUtils:
    """Allows file transfer between testing host and devices."""

    def __init__(self, device: Device):
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


class TShark:
    """TShark."""

    def __init__(self, device: Device, capfile: str = None):
        self._device = device

        # default network interface of the device
        self._interface = device.interfaces.names.pop()

        # traffic capture file
        self._capfile = capfile if capfile else "tshark.pcap"

    def start(self, filters: str = None) -> None:
        """Start packet capturing with tshark.

        Args:
            filters (str): capture filters
        """
        base_command = "tshark"
        params = {
            "-i": self._interface,
            "-f": f'"{filters}"' if filters else None,
            "-w": self._capfile,
        }
        background = "-q &"
        command = base_command
        for k, v in params.items():
            if v is not None:
                command += f" {k} {v}"
        command += f" {background}"
        self._device.tshark.execute(command)

    def stop(self) -> None:
        """Kill active tshark process running on the device."""
        self._device.tshark.execute("echo -ne '\n'")
        pid = self._device.tshark.execute("pidof tshark")
        if pid:
            command = f"kill -15 {pid}"
            self._device.tshark.execute(command + "&& echo -ne '\n'")


class TrafficCaptureConnection:
    """Connection for traffic monitoring.

    If no proxy is specified only one connection is established - to traffic source (user_endpoint)
    If proxy is specified two connections are established - to tarffic source and to the proxy host
    """

    def __init__(self, user_endpoint: Device, proxy_host: Device = None):
        # main device
        self._user = user_endpoint
        # fileutils for pcap transfer
        self._user_fileutils = FileUtils(user_endpoint)
        # tshark instance
        self._user_tshark = None

        # proxy device
        self._proxy = proxy_host
        # fileutils for pcap transfer
        self._proxy_fileutils = FileUtils(proxy_host) if proxy_host else None
        # tshark instance
        self._proxy_tshark = None

    def start_capturing(self, filters: str = None) -> None:
        # if proxy specified reconfigure filters
        if self._proxy:
            proxy_filters = filters
            user_filters = (
                "host "
                f"{self._proxy.interfaces[self._proxy_tshark._interface].ipv4.ip.compressed}"
            )

            # start capturing
            self._proxy_tshark.start(filters=proxy_filters)
            self._user_tshark.start(filters=user_filters)
        else:
            # start capturing
            self._user_tshark.start(filters=filters)

    def __enter__(self):
        # connect to devices and instantiate tshark
        self._user.connect(alias="tshark")
        self._user_tshark = TShark(self._user)

        if self._proxy:
            self._proxy.connect(alias="tshark")
            self._proxy_tshark = TShark(self._proxy)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # disconnect from devices and copy pcap files
        self._user_tshark.stop()
        self._user.tshark.disconnect()
        self._user_fileutils.copy_from_device(source=self._user_tshark._capfile)

        if self._proxy:
            self._proxy_tshark.stop()
            self._proxy.tshark.disconnect()
            self._proxy_fileutils.copy_from_device(source=self._proxy_tshark._capfile)
