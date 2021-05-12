from pyats.topology import Device


class Proxy:
    def __init__(self, device: Device):
        self._device = device

    def start(self):
        self._device.connect(alias="proxy")
        if not self.is_alive():
            self._device.proxy.execute(
                "./proxytcp/bin/proxytcp --mode default --port 1080 &"
            )
            self._device.proxy.execute("echo -ne '\n'")

    def is_alive(self):
        self._device.proxy.execute("echo -ne '\n'")
        pid = self._device.proxy.execute("pidof proxytcp")
        response = True if pid else False
        return response

    def stop(self):
        self._device.proxy.disconnect()
