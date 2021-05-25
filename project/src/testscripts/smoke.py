# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import logging
from pprint import pformat

from pyats import aetest

from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, Curl
from src.classes.analyse import BrowserResponseAnalyzer


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


class WebPageOpensInChrome(aetest.Testcase):
    @aetest.test
    def test_page_open(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != 200:
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class RemoteIPBelongsToProxy(aetest.Testcase):
    @aetest.test
    def get_remote_ip(self, user, proxy, host):
        proxy_net_ifs = proxy.interfaces.names.pop()
        proxy_ip = proxy.interfaces[proxy_net_ifs].ipv4.ip.compressed

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        remote_ip = data.get_remote_ip_port()[0]
        if remote_ip != proxy_ip:
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid remote address, expected {proxy_ip}, got {remote_ip}!"
            )


class InvalidProxyHost(aetest.Testcase):
    @aetest.test
    def connect_invalid_proxy_ip(self, user, proxy, host, proxy_ip):

        with Curl(
            client_server=user,
            proxy_server=proxy,
            session_timeout=10,
            proxy_ip=proxy_ip,
        ) as curl:
            curl.get(host)
            stats = curl.get_response()

        if "Connection timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class InvalidProxyPort(aetest.Testcase):
    @aetest.test
    def connect_invalid_proxy_port(self, user, proxy, host, proxy_port):

        with Curl(
            client_server=user,
            proxy_server=proxy,
            session_timeout=10,
            proxy_port=proxy_port,
        ) as curl:
            curl.get(host)
            stats = curl.get_response()

        if "Connection timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def stop_selenium(self, user):
        grid = SeleniumGrid(user)
        grid.stop()


if __name__ == "__main__":
    import sys
    import argparse
    import logging

    from pyats import topology

    _log.setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
