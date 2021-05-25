import os
import re
import logging

import paramiko
from paramiko import SSHClient
from scp import SCPClient
from pyats.topology import Device

import src


_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)


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
    """Interface for remote tshark command executions."""

    def __init__(self, device: Device, capfile: str = None):
        self._device = device
        self._loghead = f"TShark@{device.name}"

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
        _log.info(f"{self._loghead} - started via CLI: {command}")

    def is_alive(self):
        self._device.tshark.execute("echo -ne '\n'")
        pid = self._device.tshark.execute("pidof tshark")
        status = "ON" if pid else "OFF"
        _log.info(f"{self._loghead} - check status: {status}")
        return bool(pid)

    def stop(self) -> None:
        """Kill active tshark process running on the device."""
        self._device.tshark.execute("echo -ne '\n'")
        pid = self._device.tshark.execute("pidof tshark")
        if pid:
            command = f"kill -15 {pid}"
            self._device.tshark.execute(command + "&& echo -ne '\n'")
            _log.info(f"{self._loghead} - terminared")


class TrafficDump:
    """Connection manager for remote traffic monitoring.

    If no proxy is specified only one connection is established - to traffic source (user_endpoint)
    If proxy is specified two connections are established - to tarffic source and to the proxy host
    """

    def __init__(
        self, grid_server: Device, proxy_server: Device = None, logfile: str = None
    ):

        self._grid_server = grid_server
        self._proxy_server = proxy_server
        self._logfile = logfile

        self._grid_server.connect(alias="tshark", logfile=logfile)
        self._grid_server_dump = TShark(grid_server)
        self._grid_server_fileutils = FileUtils(grid_server)

        self._proxy_server_dump = None
        self._proxy_server_fileutils = None
        if self._proxy_server:
            self._proxy_server.connect(alias="tshark", logfile=logfile)
            self._proxy_server_dump = TShark(proxy_server)
            self._proxy_server_fileutils = FileUtils(proxy_server)

    def start_capturing(self, filters: str = None) -> None:
        # if proxy specified reconfigure filters
        if self._proxy_server:
            proxy_filters = filters
            ifs = self._proxy_server_dump._interface
            ip = self._proxy_server.interfaces[ifs].ipv4.ip.compressed
            user_filters = f"host {ip}"

            # start capturing
            self._proxy_server_dump.start(filters=proxy_filters)
            self._grid_server_dump.start(filters=user_filters)
        else:
            # start capturing
            self._grid_server_dump.start(filters=filters)

    def stop_capturing(self) -> None:
        if self._proxy_server:
            self._proxy_server_dump.stop()
            self._proxy_server.tshark.disconnect()
            self._proxy_server_fileutils.copy_from_device(
                source=self._proxy_server_dump._capfile
            )

        self._grid_server_dump.stop()
        self._grid_server.tshark.disconnect()
        self._grid_server_fileutils.copy_from_device(
            source=self._grid_server_dump._capfile
        )
