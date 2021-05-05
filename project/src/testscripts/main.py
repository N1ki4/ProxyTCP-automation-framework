# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
from pyats import aetest


from src.classes.sut import Proxy
from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome
from src.classes.analyse import BrowserResponseAnalyzer, serializer


class CommonSetup(aetest.CommonSetup):
    pass


class WebPageOpensInChrome(aetest.Testcase):
    @aetest.setup
    def start_services(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.proxy_connection = Proxy(self.proxy_device)
        self.proxy_connection.start()

        self.user_device = testbed.devices["user-1"]
        self.grid = SeleniumGrid(self.user_device)
        self.grid.start()

    @aetest.test
    def load_page(self):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host="https://wiki.archlinux.org/",
                proxy_host=self.proxy_device,
                write_pcap=False,
                timeout=30,
            )
            stats = chrome.get_stats("response.json")
        serialized_stats = serializer(stats)
        data = BrowserResponseAnalyzer(serialized_stats)
        status_code = data.get_status_code()
        if status_code != 200:
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )

    @aetest.cleanup
    def stop_services(self):
        self.proxy_connection.stop()
        self.grid.stop()


class RemoteIPBelongsToProxy(aetest.Testcase):
    @aetest.setup
    def start_services(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.proxy_connection = Proxy(self.proxy_device)
        self.proxy_connection.start()

        self.user_device = testbed.devices["user-1"]
        self.grid = SeleniumGrid(self.user_device)
        self.grid.start()

    @aetest.test
    def get_remote_ip(self):
        proxy_net_ifs = self.proxy_device.interfaces.names.pop()
        proxy_ip = self.proxy_device.interfaces[proxy_net_ifs].ipv4.ip.compressed

        with Chrome(self.user_device) as chrome:
            chrome.open(
                host="https://wiki.archlinux.org/",
                proxy_host=self.proxy_device,
                write_pcap=False,
                timeout=30,
            )
            stats = chrome.get_stats("response.json")
        serialized_stats = serializer(stats)
        data = BrowserResponseAnalyzer(serialized_stats)
        remote_ip = data.get_remote_ip_port()[0]

        if remote_ip != proxy_ip:
            self.failed(
                f"Invalid remote address, expected {proxy_ip}, got {remote_ip}!"
            )

    @aetest.cleanup
    def stop_services(self):
        self.proxy_connection.stop()
        self.grid.stop()


class CommonCleanup(aetest.CommonCleanup):
    pass


if __name__ == "__main__":
    import sys
    import argparse
    import logging

    from pyats import topology

    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.ERROR)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
