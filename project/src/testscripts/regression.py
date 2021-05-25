# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
from pyats import aetest
import logging


from src.classes.remote_tools import SeleniumGrid
from src.classes.sut import Proxy
from src.classes.clients import Chrome


_log = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def update_testscript_parameters(self, testbed):
        user_device = testbed.devices["user-2"]
        proxy_device = testbed.devices["proxy-vm"]
        self.parent.parameters.update(
            {
                "user": user_device,
                "proxy": proxy_device,
            }
        )

    @aetest.subsection
    def start_selenium(self, user):
        grid = SeleniumGrid(user)
        grid.start()


class ProxyShutAfterCacheCleaning(aetest.Testcase):

    parameters = {"host": "https://docs.docker.com/", "cleanings": 5}

    @aetest.setup
    def setup(self, proxy):
        self.proxy_connection = Proxy(proxy)
        self.proxy_connection.start()

    @aetest.test
    def test_cache_cleaning(self, user, host, cleanings):

        for i in range(1, cleanings + 1):
            with Chrome(grid_server=user, session_wide_proxy=False) as chrome:
                chrome.get(host)
            if not self.proxy_connection.is_alive():
                self.failed(f"Proxy server shuted down after session `{i}`")

    @aetest.cleanup
    def cleanup(self):
        self.proxy_connection.stop()


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def stop_selenium(self, user):
        grid = SeleniumGrid(user)
        grid.stop()


if __name__ == "__main__":
    import sys
    import argparse

    from pyats import topology

    _log.setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
