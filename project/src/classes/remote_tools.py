from pyats.topology import Device


class SeleniumGrid:
    def __init__(self, device: Device):
        self._device = device

    def start(self):
        self._device.connect(alias="grid")
        self._device.grid.execute("docker-compose start")

    def stop(self):
        self._device.grid.execute("docker-compose stop")
        self._device.grid.disconnect()
