# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import logging
import statistics
from pprint import pformat

from pyats import aetest

from src.classes.remote_tools import SeleniumGrid
from src.classes.sut import Proxy
from src.classes.clients import Chrome, ChromeAsync
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


class ProxyDoesntShutAfterCacheCleaning(aetest.Testcase):
    @aetest.setup
    def setup(self, proxy):
        self.proxy_connection = Proxy(proxy)
        self.proxy_connection.start()

    @aetest.test
    def test_cache_cleaning(self, proxy, user, host, cleanings):

        for i in range(1, cleanings + 1):
            with Chrome(
                grid_server=user, proxy_server=proxy, session_wide_proxy=False
            ) as chrome:
                chrome.get(host)
            if not self.proxy_connection.is_alive():
                self.failed(f"Proxy server shuted down after session `{i}`")

    @aetest.cleanup
    def cleanup(self):
        self.proxy_connection.stop()


class ProxyDoesNotAlterPorts(aetest.Testcase):
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
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
            _log.info(f"Web Brower logs:\n{pformat(stats)}")
            self.failed("Invalod response, no `ERR_CONNECTION_REFUSED` occured!")


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
