# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import statistics
import logging
from pprint import pformat

from pyats import aetest

from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, ChromeAsync
from src.classes.page_objects import AuthPage, PageForNavigation
from src.classes.analyse import BrowserResponseAnalyzer
from src.classes.formatters import log_table_time, log_table_resources


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
        self.parent.parameters.update({"grid": grid})
        grid.start()


class HostSupportCloudFlare(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportApache(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportNginx(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportMicrosoftIIS(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportGWS(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class HostSupportAmazon(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed(
                f"Invalid response, expected status code 200, got {status_code}!"
            )


class WebsiteResourcesLoading(aetest.Testcase):
    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(
            self.count_page_resources,
            uids=self.parameters["sections_uids"],
            host=self.parameters["hosts"],
            pass_rate=self.parameters["pass_rates"],
        )

    @aetest.test
    def count_page_resources(self, steps, proxy, user, host, runs, pass_rate):

        direct = []
        with steps.start("Loading page: colecting stats with proxy off"):
            for _ in range(runs):
                with Chrome(grid_server=user) as chrome:
                    chrome.get(host)
                    stats = chrome.get_stats()

                data = BrowserResponseAnalyzer(stats)
                direct.append(
                    [
                        (
                            data.get_requests_statistics(),
                            data.get_response_statistics(),
                        ),
                    ]
                )

        proxyied = []
        with steps.start("Loading page: colecting stats with proxy on"):
            for _ in range(runs):
                with Chrome(grid_server=user, proxy_server=proxy) as chrome:
                    chrome.get(host)
                    stats = chrome.get_stats()

                data = BrowserResponseAnalyzer(stats)
                proxyied.append(
                    [
                        (
                            data.get_requests_statistics(),
                            data.get_response_statistics(),
                        ),
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

            console_log = log_table_resources(
                hosts=(host,),
                runs=runs,
                direct_stats=direct_stats,
                proxyied_stats=proxyied_stats,
                request_avg_success=rates_req,
                response_avg_success=rates_rsp,
            )

            _log.info(console_log)
            if not pass_condition:
                self.failed("To many resources were lost", goto=["next_tc"])


class ReloadingLightWebpage(aetest.Testcase):
    @aetest.test
    def test_reloading(self, steps, proxy, user, runs, host, pass_rate):

        direct_stats = []
        with steps.start("Reloading: colecting stats with proxy off"):
            with Chrome(grid_server=user) as chrome:
                chrome.get(host)
                for _ in range(runs):
                    chrome.refresh()
                stats = chrome.get_stats()
            data = BrowserResponseAnalyzer(stats)
            direct_stats.append(
                (data.get_requests_statistics(), data.get_response_statistics())
            )

        proxyied_stats = []
        with steps.start("Reloading: colecting stats with proxy on"):
            with Chrome(grid_server=user, proxy_server=proxy) as chrome:
                chrome.get(host)
                for _ in range(runs):
                    chrome.refresh()
                stats = chrome.get_stats()
            data = BrowserResponseAnalyzer(stats)
            proxyied_stats.append(
                (data.get_requests_statistics(), data.get_response_statistics())
            )

        with steps.start("Anylizing results"):

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

            console_log = log_table_resources(
                hosts=(host,),
                runs=runs,
                direct_stats=direct_stats,
                proxyied_stats=proxyied_stats,
                request_avg_success=rates_req,
                response_avg_success=rates_rsp,
            )

            _log.info(console_log)
            if not pass_condition:
                self.failed("Too many resources were lost during reloading!")


class ChainNavigation(aetest.Testcase):
    @aetest.test
    def test_navigation(self, proxy, user, xpaths):

        with PageForNavigation(grid_server=user, proxy_server=proxy) as page:
            page.get()
            for xpath in xpaths:
                page.locate_element_by_xpath_and_click(xpath)
                if not page.is_document_ready():
                    self.failed("Document is not ready on first navigating!")


class LoadingTime(aetest.Testcase):
    @aetest.setup
    def setup_loops(self):
        aetest.loop.mark(
            self.loading_time_test,
            uids=self.parameters["sections_uids"],
            host=self.parameters["hosts"],
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
                time_proxy_on.append(time)

        with steps.start("Comparing results"):
            rates = [y / x for x, y in zip(time_proxy_off, time_proxy_on)]
            overtime_entries = [i for i in rates if i > delay_rate]

            console_log = log_table_time(
                host=host,
                runs=runs,
                proxyied_times=time_proxy_on,
                direct_times=time_proxy_off,
                avg_success=rates,
            )

            _log.info(console_log)
            if len(overtime_entries) > fails:
                self.failed(
                    f"{len(overtime_entries)} out of {runs} times page loading"
                    " time with proxy on exceeded normal loading time for more than"
                    f" {delay_rate} times",
                    goto=["next_tc"],
                )


class AuthenticationOAUTH(aetest.Testcase):
    @aetest.test
    def test_login(self, proxy, user, email, services_pass, mailbox_pass):

        with AuthPage(grid_server=user, proxy_server=proxy) as page:
            page.get()
            page.oauth_login(
                mail=email, password=services_pass, box_password=mailbox_pass
            )
            result = page.check_auth()
            stats = page.get_stats()

        if result is False:
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed("Login failed")


class AuthenticationPassword(aetest.Testcase):
    @aetest.test
    def test_login(self, proxy, user, email, services_pass):

        with AuthPage(grid_server=user, proxy_server=proxy) as page:
            page.get()
            page.login(
                mail=email,
                password=services_pass,
            )
            result = page.check_auth()
            stats = page.get_stats()

        if result is False:
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed("Login failed")


class MultipleTabsLoading(aetest.Testcase):
    @aetest.setup
    def restart_grid(self, grid):
        grid.restart()

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

            console_log = log_table_resources(
                hosts=hosts,
                runs=runs,
                direct_stats=direct_stats,
                proxyied_stats=proxyied_stats,
                request_avg_success=rates_req,
                response_avg_success=rates_rsp,
            )

            _log.info(console_log)
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

    from pyats import topology

    _log.setLevel(logging.DEBUG)
    logging.getLogger("unicon").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
