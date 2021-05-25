import logging

from pyats.topology import Device


_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)


class Proxy:
    def __init__(self, device: Device, logfile: str = None):
        self._device = device
        self._loghead = f"ProxyServer(SUT)@{device.name}"
        self._logfile = logfile

    def start(self):
        self._device.connect(alias="proxy", logfile=self._logfile)
        if not self.is_alive():
            command = "./proxytcp/bin/proxytcp --mode default --port 1080 &"
            self._device.proxy.execute(command)
            _log.info(f"{self._loghead} - started via CLI: {command}")

    def is_alive(self):
        self._device.proxy.execute("echo -ne '\n'")
        pid = self._device.proxy.execute("pidof proxytcp")
        status = "ON" if pid else "OFF"
        _log.info(f"{self._loghead} - check status: {status}")
        return bool(pid)

    def stop(self):
        self._device.proxy.disconnect()
        _log.info(f"{self._loghead} - disconnected")
