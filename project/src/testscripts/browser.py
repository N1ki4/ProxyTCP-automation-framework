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
    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test.loop(
        uids=["light_web_page", "medium_web_page", "heavy_web_page"],
        host=[
            "https://pypi.org/project/pyats/",
            "https://docs.docker.com/",
            "https://www.skype.com/",
        ],
    )
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


class SuperLightWebpageResourceLoading(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test.loop(
        uids=[
            "first_run",
            "second_run",
            "third_run",
            "fourth_run",
            "fifth_run",
            "sixth_run",
            "seventh_run",
            "eighth_run",
            "ninth_run",
            "tenth_run",
        ]
    )
    def compare_page_resources(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
                write_pcap=False,
                timeout=30,
            )

            stats = chrome.get_stats()
            serialized_stats = serializer(stats)
            data = BrowserResponseAnalyzer(serialized_stats)
            requests = BrowserResponseAnalyzer.get_requests_statistics(data)
            responses = BrowserResponseAnalyzer.get_response_statistics(data)
            failed = BrowserResponseAnalyzer.get_loading_failed_statistics(data)

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
            proxy_requests = BrowserResponseAnalyzer.get_requests_statistics(data)
            proxy_responses = BrowserResponseAnalyzer.get_response_statistics(data)
            proxy_failed = BrowserResponseAnalyzer.get_loading_failed_statistics(data)

            if not (
                (requests, responses, failed)
                == (proxy_requests, proxy_responses, proxy_failed)
                or (requests, responses + 1, failed)
                == (proxy_requests, proxy_responses, proxy_failed)
                or (requests, responses, failed)
                == (proxy_requests, proxy_responses + 1, proxy_failed)
            ):
                self.failed("Too many resources were lost!")


class LoadingTimeSuperLight(aetest.Testcase):

    parameters = {
        "host": "https://wiki.archlinux.org/",
        "delay_rate": 2,
        "runs": 10,
        "fails": 2,
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def loading_time_test(self, steps, host, delay_rate, runs, fails):
        time_proxy_off = []
        with steps.start("Collecting statistics with proxy off"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_off.append(stats)

        time_proxy_on = []
        with steps.start("Collecting statistics with proxy on"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        proxy_host=self.proxy_device,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_on.append(stats)

        with steps.start("Comparing results"):
            overtime_entries = list(
                filter(
                    lambda r: r > delay_rate,
                    map(lambda x, y: y / x, time_proxy_off, time_proxy_on),
                )
            )
            if len(overtime_entries) > fails:
                self.failed(
                    f"{len(overtime_entries)} out of {runs} times page loading"
                    " time with proxy on exceeded normal loading time for more than"
                    f" {delay_rate} times"
                )


class LoadingTimeLight(aetest.Testcase):

    parameters = {
        "host": "https://docs.docker.com/",
        "delay_rate": 2,
        "runs": 10,
        "fails": 2,
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def loading_time_test(self, steps, host, delay_rate, runs, fails):
        time_proxy_off = []
        with steps.start("Collecting statistics with proxy off"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_off.append(stats)

        time_proxy_on = []
        with steps.start("Collecting statistics with proxy on"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        proxy_host=self.proxy_device,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_on.append(stats)

        with steps.start("Comparing results"):
            overtime_entries = list(
                filter(
                    lambda r: r > delay_rate,
                    map(lambda x, y: y / x, time_proxy_off, time_proxy_on),
                )
            )
            if len(overtime_entries) > fails:
                self.failed(
                    f"{len(overtime_entries)} out of {runs} times page loading"
                    " time with proxy on exceeded normal loading time for more than"
                    f" {delay_rate} times"
                )


class LoadingTimeMedium(aetest.Testcase):

    parameters = {
        "host": "https://glossary.istqb.org/app/en/search/",
        "delay_rate": 2,
        "runs": 10,
        "fails": 2,
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def loading_time_test(self, steps, host, delay_rate, runs, fails):
        time_proxy_off = []
        with steps.start("Collecting statistics with proxy off"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_off.append(stats)

        time_proxy_on = []
        with steps.start("Collecting statistics with proxy on"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        proxy_host=self.proxy_device,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_on.append(stats)

        with steps.start("Comparing results"):
            overtime_entries = list(
                filter(
                    lambda r: r > delay_rate,
                    map(lambda x, y: y / x, time_proxy_off, time_proxy_on),
                )
            )
            if len(overtime_entries) > fails:
                self.failed(
                    f"{len(overtime_entries)} out of {runs} times page loading"
                    " time with proxy on exceeded normal loading time for more than"
                    f" {delay_rate} times"
                )


class LoadingTimeHeavy(aetest.Testcase):

    parameters = {
        "host": "https://www.skype.com",
        "delay_rate": 2,
        "runs": 10,
        "fails": 2,
    }

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def loading_time_test(self, steps, host, delay_rate, runs, fails):
        time_proxy_off = []
        with steps.start("Collecting statistics with proxy off"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_off.append(stats)

        time_proxy_on = []
        with steps.start("Collecting statistics with proxy on"):
            for _ in range(runs):
                with Chrome(self.user_device) as chrome:
                    chrome.open(
                        host=host,
                        proxy_host=self.proxy_device,
                        timeout=30,
                        write_pcap=False,
                    )
                    stats = chrome._get_page_loading_time()
                    print(stats)
                    time_proxy_on.append(stats)

        with steps.start("Comparing results"):
            overtime_entries = list(
                filter(
                    lambda r: r > delay_rate,
                    map(lambda x, y: y / x, time_proxy_off, time_proxy_on),
                )
            )
            if len(overtime_entries) > fails:
                self.failed(
                    f"{len(overtime_entries)} out of {runs} times page loading"
                    " time with proxy on exceeded normal loading time for more than"
                    f" {delay_rate} times"
                )


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def stop_selenium(self, testbed):
        user_device = testbed.devices["user-1"]
        grid = SeleniumGrid(user_device)
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
