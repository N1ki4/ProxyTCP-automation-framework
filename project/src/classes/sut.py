from pyats.topology import Device


class Proxy:
    def __init__(self, device: Device):
        self._device = device

    def start(self):
        self._device.connect(alias="proxy")
        self._device.proxy.execute(
            "./proxytcp/bin/proxytcp --mode default --port 1080 &"
        )
        self._device.proxy.execute("echo -ne '\n'")

    def stop(self):
        self._device.proxy.disconnect()
