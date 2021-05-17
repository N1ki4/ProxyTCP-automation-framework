# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, Curl
from src.classes.analyse import BrowserResponseAnalyzer


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

    parameters = {"host": "https://wiki.archlinux.org/"}

    @aetest.test
    def test_page_open(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != 200:
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class RemoteIPBelongsToProxy(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org/"}

    @aetest.test
    def get_remote_ip(self, user, proxy, host):
        proxy_net_ifs = proxy.interfaces.names.pop()
        proxy_ip = proxy.interfaces[proxy_net_ifs].ipv4.ip.compressed

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats("file.json")

        data = BrowserResponseAnalyzer(stats)
        remote_ip = data.get_remote_ip_port()[0]
        if remote_ip != proxy_ip:
            self.failed(
                f"Invalid remote address, expected {proxy_ip}, got {remote_ip}!"
            )


class ProxyDoesNotAlterPorts(aetest.Testcase):

    parameters = {
        "no_error": ["https://tools.ietf.org", "https://tools.ietf.org:443"],
        "ssl_error": ["https://tools.ietf.org:80"],
        "connection_error": [
            "https://tools.ietf.org:20222",
            "https://tools.ietf.org:65535",
        ],
    }

    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(self.no_error_test, host=self.parameters["no_error"])
        aetest.loop.mark(self.ssl_error_test, host=self.parameters["ssl_error"])
        aetest.loop.mark(self.con_error_test, host=self.parameters["connection_error"])

    @aetest.test
    def no_error_test(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != 200:
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )

    @aetest.test
    def ssl_error_test(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        errors = data.get_browser_errors()
        pass_condition = len(errors) == 1 and "ERR_SSL_PROTOCOL_ERROR" in errors[0]
        if not pass_condition:
            self.failed("Invalod response, no `ERR_SSL_PROTOCOL_ERROR` occured!")

    @aetest.test
    def con_error_test(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        errors = data.get_browser_errors()
        pass_condition = len(errors) == 1 and "ERR_CONNECTION_REFUSED" in errors[0]
        if not pass_condition:
            self.failed("Invalod response, no `ERR_CONNECTION_REFUSED` occured!")


class InvalidProxyHost(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org/", "proxy_ip": "10.1.1.1"}

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

        if "Operation timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class InvalidProxyPort(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org/", "proxy_port": "8010"}

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

        if "Operation timed out" not in stats:
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

    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.ERROR)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
