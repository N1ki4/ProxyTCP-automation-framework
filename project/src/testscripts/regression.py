# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.sut import Proxy
from src.classes.clients import Chrome


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def start_selenium(self, testbed):
        user_device = testbed.devices["user-2"]
        grid = SeleniumGrid(user_device)
        grid.start()


class ProxyShutAfterCacheCleaning(aetest.Testcase):

    parameters = {"host": "https://docs.docker.com/", "cleanings": 5}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-2"]

        self.proxy_connection = Proxy(self.proxy_device)
        self.proxy_connection.start()

    @aetest.test
    def test_cache_cleaning(self, host, cleanings):
        for i in range(1, cleanings + 1):
            with Chrome(device=self.user_device, single_session_proxy=False) as chrome:
                chrome.open(
                    host=host,
                    proxy_host=self.proxy_device,
                    timeout=30,
                    write_pcap=False,
                )
            if not self.proxy_connection.is_alive():
                self.failed(f"Proxy server shuted down after session `{i}`")


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def stop_selenium(self, testbed):
        user_device = testbed.devices["user-2"]
        grid = SeleniumGrid(user_device)
        grid.stop()


if __name__ == "__main__":
    import sys
    import argparse
    import logging

    from pyats import topology

    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
