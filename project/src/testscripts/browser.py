# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import statistics


from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, ChromeAsync
from src.classes.page_objects import AuthPage, PageForNavigation
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


class HostSupportCloudFlare(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://unpkg.com/",
            "https://www.allaboutcookies.org/",
            "https://forums.wxwidgets.org/",
        ]
    }

    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(self.cloud_flare_test, host=self.parameters["hosts"])

    @aetest.test
    def cloud_flare_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
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
    def setup_loops(self):
        aetest.loop.mark(self.apache_test, host=self.parameters["hosts"])

    @aetest.test
    def apache_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
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
    def setup_loops(self):
        aetest.loop.mark(self.nginx_test, host=self.parameters["hosts"])

    @aetest.test
    def nginx_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
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
    def setup_loops(self):
        aetest.loop.mark(self.microsoft_iis_test, host=self.parameters["hosts"])

    @aetest.test
    def microsoft_iis_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != 200:
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportGWS(aetest.Testcase):

    parameters = {"hosts": ["https://www.google.com/", "https://golang.google.cn/"]}

    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(self.gws_test, host=self.parameters["hosts"])

    @aetest.test
    def gws_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
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
    def setup_loops(self):
        aetest.loop.mark(self.amazon_test, host=self.parameters["hosts"])

    @aetest.test
    def amazon_test(self, proxy, user, host):

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != 200:
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class WebsiteResourcesLoading(aetest.Testcase):
    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(
            self.count_page_resources,
            uids=["light_web_page", "medium_web_page", "heavy_web_page"],
            host=[
                "https://pypi.org/project/pyats/",
                "https://docs.docker.com/",
                "https://www.skype.com/",
            ],
        )

    def count_page_resources(self, proxy, user, host):
        req_run_result = []
        resp_run_result = []

        for _ in range(1, 6):
            with Chrome(grid_server=user) as chrome:
                chrome.get(host)
                stats = chrome.get_stats()

            data = BrowserResponseAnalyzer(stats)
            req_run_result.append(BrowserResponseAnalyzer.get_requests_statistics(data))
            resp_run_result.append(
                BrowserResponseAnalyzer.get_response_statistics(data)
            )

        for _ in range(1, 6):
            with Chrome(grid_server=user, proxy_server=proxy) as chrome:
                chrome.get(host)
                stats = chrome.get_stats()

            data = BrowserResponseAnalyzer(stats)
            req_run_result.append(BrowserResponseAnalyzer.get_requests_statistics(data))
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
    def setup_loops(self):
        aetest.loop.mark(
            self.compare_page_resources,
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
            ],
        )

    def compare_page_resources(self, proxy, user, host):

        with Chrome(grid_server=user) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        requests = BrowserResponseAnalyzer.get_requests_statistics(data)
        responses = BrowserResponseAnalyzer.get_response_statistics(data)
        failed = BrowserResponseAnalyzer.get_loading_failed_statistics(data)

        with Chrome(grid_server=user, proxy_server=proxy) as chrome:
            chrome.get(host)
            stats = chrome.get_stats()

        data = BrowserResponseAnalyzer(stats)
        proxy_requests = BrowserResponseAnalyzer.get_requests_statistics(data)
        proxy_responses = BrowserResponseAnalyzer.get_response_statistics(data)
        proxy_failed = BrowserResponseAnalyzer.get_loading_failed_statistics(data)

        pass_condition_1 = (
            requests,
            responses,
            failed == proxy_requests,
            proxy_responses,
            proxy_failed,
        )
        pass_condition_2 = (
            requests,
            responses + 1,
            failed == proxy_requests,
            proxy_responses,
            proxy_failed,
        )
        pass_condition_3 = (
            requests,
            responses,
            failed == proxy_requests,
            proxy_responses + 1,
            proxy_failed,
        )
        if not (pass_condition_1 or pass_condition_2 or pass_condition_3):
            self.failed("Too many resources were lost!")


class ReloadingLightWebpage(aetest.Testcase):

    parameters = {"runs": 3, "host": "https://docs.docker.com/", "pass_rate": 0.95}

    @aetest.test
    def test_reloading(self, steps, proxy, user, runs, host, pass_rate):

        direct = None
        with steps.start("Reloading: colecting stats with proxy off"):
            with Chrome(grid_server=user) as chrome:
                chrome.get(host)
                for _ in range(runs):
                    chrome.refresh()
                stats = chrome.get_stats()
            data = BrowserResponseAnalyzer(stats)
            direct = (data.get_requests_statistics(), data.get_response_statistics())

        proxyied = None
        with steps.start("Reloading: colecting stats with proxy on"):
            with Chrome(grid_server=user, proxy_server=proxy) as chrome:
                chrome.get(host)
                for _ in range(runs):
                    chrome.refresh()
                stats = chrome.get_stats()
            data = BrowserResponseAnalyzer(stats)
            proxyied = (data.get_requests_statistics(), data.get_response_statistics())

        with steps.start("Anylizing results"):

            if proxyied == (0, 0):
                self.aborted("Proxy server connection lost during the session")

            rate_req = proxyied[0] / direct[0]
            rate_rsp = proxyied[1] / direct[1]
            pass_condition = rate_req >= pass_rate and rate_rsp >= pass_rate
            if not pass_condition:
                self.failed("Too many resources were lost while second reloading!")


class ChainNavigation(aetest.Testcase):

    parameters = {
        "xpaths": ['//*[@id="ca-history"]/a', '//*[@id="mw-content-text"]/div/p/a']
    }

    @aetest.test
    def test_navigation(self, proxy, user, xpaths):

        with PageForNavigation(grid_server=user, proxy_server=proxy) as page:
            page.get()
            for xpath in xpaths:
                page.locate_element_by_xpath_and_click(xpath)
                if not page.is_document_ready():
                    self.failed("Document is not ready on first navigating!")


class LoadingTime(aetest.Testcase):

    parameters = {
        "delay_rate": 2,
        "runs": 10,
        "fails": 2,
    }

    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(
            self.loading_time_test,
            uids=["superlight_page", "light_page", "medium_page", "heavy_page"],
            host=[
                "https://wiki.archlinux.org/",
                "https://docs.docker.com/",
                "https://glossary.istqb.org/app/en/search/",
                "https://www.skype.com",
            ],
        )

    @aetest.test
    def loading_time_test(self, steps, proxy, user, host, delay_rate, runs, fails):

        time_proxy_off = []
        with steps.start("Collecting statistics with proxy off"):
            for _ in range(runs):
                with Chrome(grid_server=user) as chrome:
                    chrome.get(host)
                    time = chrome._get_page_loading_time()
                time_proxy_off.append(time)

        time_proxy_on = []
        with steps.start("Collecting statistics with proxy on"):
            for _ in range(runs):
                with Chrome(grid_server=user, proxy_server=proxy) as chrome:
                    chrome.get(host)
                    time = chrome._get_page_loading_time()
                time_proxy_off.append(time)

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
                    f" {delay_rate} times",
                    goto=["next_tc"],
                )


class AuthenticationOAUTH(aetest.Testcase):

    parameters = {
        "email": "junkmail.dp.ua@gmail.com",
        "services_pass": "OtcVs114aqE",
        "mailbox_pass": "OtcVs114aqQ",
    }

    @aetest.test
    def test_login(self, proxy, user, email, services_pass, mailbox_pass):

        with AuthPage(grid_server=user, proxy_server=proxy) as page:
            page.get()
            page.oauth_login(
                mail=email, password=services_pass, box_password=mailbox_pass
            )
            result = page.check_auth()

        if result is False:
            self.failed("Login failed")


class AuthenticationPassword(aetest.Testcase):

    parameters = {"email": "junkmail.dp.ua@gmail.com", "services_pass": "OtcVs114aqE"}

    @aetest.test
    def test_login(self, proxy, user, email, services_pass):

        with AuthPage(grid_server=user, proxy_server=proxy) as page:
            page.get()
            page.login(
                mail=email,
                password=services_pass,
            )
            result = page.check_auth()

        if result is False:
            self.failed("Login failed")


class MultipleTabsLoading(aetest.Testcase):

    parameters = {
        "runs": 5,
        "hosts": [
            "https://dev.mysql.com/doc/refman/8.0/en/",
            "https://tools.ietf.org/",
            "https://docs.docker.com/",
        ],
        "pass_rate": 0.85,
    }

    @aetest.test
    def test_multitab_loading(self, steps, proxy, user, runs, hosts, pass_rate):

        direct = []
        with steps.start("Loading multiple tabs: colecting stats with proxy off"):
            for _ in range(runs):
                with ChromeAsync(grid_server=user) as chrome:
                    chrome.get(hosts)
                    stats = chrome.get_stats()

                data = (BrowserResponseAnalyzer(stat) for stat in stats)
                direct.append(
                    [
                        (resp.get_requests_statistics(), resp.get_response_statistics())
                        for resp in data
                    ]
                )

        proxyied = []
        with steps.start("Loading multiple tabs: colecting stats with proxy on"):
            for _ in range(runs):
                with ChromeAsync(grid_server=user, proxy_server=proxy) as chrome:
                    chrome.get(hosts)
                    stats = chrome.get_stats()

                data = (BrowserResponseAnalyzer(stat) for stat in stats)
                proxyied.append(
                    [
                        (resp.get_requests_statistics(), resp.get_response_statistics())
                        for resp in data
                    ]
                )

        with steps.start("Anylizing results"):

            direct_stats = []
            for entry in zip(*direct):
                mean_req = statistics.mean(stat[0] for stat in entry)
                mean_rsp = statistics.mean(stat[1] for stat in entry)
                direct_stats.append((mean_req, mean_rsp))

            proxyied_stats = []
            for entry in zip(*proxyied):
                mean_req = statistics.mean(stat[0] for stat in entry)
                mean_rsp = statistics.mean(stat[1] for stat in entry)
                proxyied_stats.append((mean_req, mean_rsp))

            rates_req = [
                tup1[0] / tup2[0]
                for tup1, tup2 in zip(proxyied_stats, direct_stats)
                if tup2[0] != 0
            ]
            rates_rsp = [
                tup1[1] / tup2[1]
                for tup1, tup2 in zip(proxyied_stats, direct_stats)
                if tup2[1] != 0
            ]
            pass_condition = all(rate >= pass_rate for rate in rates_req) and all(
                rate >= pass_rate for rate in rates_rsp
            )
            if not pass_condition:
                self.failed("To many resources were lost")


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
