# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome
from src.classes.analyse import (
    BrowserResponseAnalyzer,
    serializer,
)


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def start_selenium(self, testbed):
        user_device = testbed.devices["user-1"]
        grid = SeleniumGrid(user_device)
        grid.start()


class HostSupportCloudFlare(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://unpkg.com/",
            "https://www.allaboutcookies.org/",
            "https://forums.wxwidgets.org/",
        ]
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.cloud_flare_test, host=self.parameters["hosts"])

    @aetest.test
    def cloud_flare_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class HostSupportApache(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://tools.ietf.org/html/rfc1928",
            "https://w3techs.com/technologies/details/ws-apache",
            "https://dev.mysql.com/doc/refman/8.0/en/",
        ]
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.apache_test, host=self.parameters["hosts"])

    @aetest.test
    def apache_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class HostSupportNginx(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://pypi.org/project/pyats/",
            "https://wiki.archlinux.org/",
            "https://glossary.istqb.org/app/en/search/",
        ]
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.nginx_test, host=self.parameters["hosts"])

    @aetest.test
    def nginx_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class HostSupportMicrosoftIIS(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://www.skype.com/en/about/",
            "https://stackexchange.com/",
            "https://stackoverflow.com/questions/9436534/ajax-tutorial-for-post-and-get",
        ]
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.microsoft_iis_test, host=self.parameters["hosts"])

    @aetest.test
    def microsoft_iis_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class HostSupportGWS(aetest.Testcase):

    parameters = {"hosts": ["https://www.google.com/", "https://golang.google.cn/"]}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.gws_test, host=self.parameters["hosts"])

    @aetest.test
    def gws_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class HostSupportAmazon(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://developer.mozilla.org/uk/docs/Learn/Server-side/Django",
            "https://docs.docker.com/",
        ]
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(self.amazon_test, host=self.parameters["hosts"])

    @aetest.test
    def amazon_test(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
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


class WebsiteResourcesLoading(aetest.Testcase):

    parameters = {"host": "https://docs.docker.com/"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def count_page_resources(self, host):
        req_run_result = []
        resp_run_result = []
        for _ in range(1, 6):
            with Chrome(self.user_device) as chrome:
                chrome.open(
                    host=host,
                    write_pcap=False,
                    timeout=30,
                )
                stats = chrome.get_stats()
                serialized_stats = serializer(stats)
                data = BrowserResponseAnalyzer(serialized_stats)
                req_run_result.append(
                    BrowserResponseAnalyzer.get_requests_statistics(data)
                )
                resp_run_result.append(
                    BrowserResponseAnalyzer.get_response_statistics(data)
                )

        for _ in range(1, 6):
            with Chrome(self.user_device) as chrome:
                chrome.open(
                    host=host,
                    proxy_host=self.proxy_device,
                    write_pcap=False,
                    timeout=30,
                )
                stats = chrome.get_stats()
                serialized_stats = serializer(stats)
                data = BrowserResponseAnalyzer(serialized_stats)
                req_run_result.append(
                    BrowserResponseAnalyzer.get_requests_statistics(data)
                )
                resp_run_result.append(
                    BrowserResponseAnalyzer.get_response_statistics(data)
                )
        disabled_proxy_requests_slice = req_run_result[: int(len(req_run_result) / 2)]
        enable_proxy_requests_slice = req_run_result[int(len(req_run_result) / 2) :]

        disabled_proxy_response_slice = resp_run_result[: int(len(resp_run_result) / 2)]
        enable_proxy_response_slice = resp_run_result[int(len(resp_run_result) / 2) :]

        avg_disabled_proxy_request = sum(disabled_proxy_requests_slice) / len(
            disabled_proxy_requests_slice
        )
        avg_enable_proxy_request = sum(enable_proxy_requests_slice) / len(
            enable_proxy_requests_slice
        )
        req_percent = (avg_enable_proxy_request * 100) / avg_disabled_proxy_request

        avg_no_proxy_resp = sum(disabled_proxy_response_slice) / len(
            disabled_proxy_response_slice
        )
        avg_enable_proxy_resp = sum(enable_proxy_response_slice) / len(
            enable_proxy_response_slice
        )
        resp_percent = (100 * avg_enable_proxy_resp) / avg_no_proxy_resp

        if int(round(req_percent)) < 95 and int(round(resp_percent)) < 95:
            self.failed("Too many resources were lost with proxy enabled")


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
