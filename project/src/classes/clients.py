import re
import json
import socket
import logging
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from abc import ABC

from selenium import webdriver
from selenium.common import exceptions
from pyats.topology import Device

from src.classes import utils
from src.classes.sut import Proxy
from src.classes.analyse import BrowserStatKeys

_log = logging.getLogger(__name__).setLevel(logging.INFO)
logging.getLogger("unicon").setLevel(logging.INFO)


def get_host_ip(host) -> str:
    """Retrieve IP of the host to set capture filters in tshark."""
    host = re.compile(r"(http|https)://((\w+(-)?\w+\.)+\w+)").search(host)[2]
    return socket.gethostbyname(host)


class ChromeBase(ABC):
    """ChromeBase.

    Context manager which inplements chrome functionality
    and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(self, device: Device, options: list, single_session_proxy: bool):
        """Constructor.

        Args:
            device (Device): device object, which grid will be triggered
            options (list): options for chrome as command line arguments
            pcap_file (str): file on the device where to store traffic capture
            single_session_proxy (bool): enabe proxy switching on the session level
        """

        self._device = device
        self._singele_session_proxy = single_session_proxy
        self._chromeoptions = options
        self._grid = None
        self._proxy_enabled = False
        self._proxy_connection = None
        self._exceptions = []

        # apply options
        chromeoptions = webdriver.ChromeOptions()
        if isinstance(options, list):
            for entry in options:
                chromeoptions.add_argument(entry)
        self._chromeoptions = chromeoptions

        # enable logging (do not change)
        self._chromeoptions.capabilities["goog:loggingPrefs"] = {
            "performance": "ALL",
            "browser": "ALL",
        }

        # identify selenium grid
        connection = self._device.connections.cli.command
        host = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[3]
        grid = f"http://{host}:4444/wd/hub"
        self._grid = grid

    def _set_proxy(
        self, proxy_ip: str, proxy_port: str = None, proxy_protocol: str = None
    ) -> None:
        """Set proxy servere parameters.

        Args:
            proxy_ip (str): ip address of the proxy host
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            proxy_protocol (str): proxy protocol, default socks5
        """
        proxy_protocol = "socks5" if proxy_protocol is None else proxy_protocol
        proxy_port = "1080" if proxy_port is None else proxy_port
        option = f"--proxy-server={proxy_protocol}://{proxy_ip}:{proxy_port}"
        self._add_option(option)
        self._proxy_enabled = True

    def _start_proxy(self, proxy_host: Device):
        self._proxy_connection = Proxy(proxy_host)
        self._proxy_connection.start()

    def _stop_proxy(self):
        self._proxy_connection.stop()

    def _add_option(self, option: str) -> None:
        self._chromeoptions.add_argument(option)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass


class Chrome(ChromeBase):
    """Chrome.

    Single driver Chrome session manager.
    """

    def __init__(
        self, device: Device, options: list = None, single_session_proxy: bool = True
    ):
        super().__init__(device, options, single_session_proxy)
        self._driver = None

    def _init_driver(self):
        """Initialize driver."""
        self._driver = webdriver.Remote(
            command_executor=self._grid, options=self._chromeoptions
        )

    def _get(self, host: str, timeout: int):
        """Execute driver.get method with explicitly provided timeout."""
        if isinstance(timeout, int):
            self._driver.implicitly_wait(timeout)
        try:
            self._driver.get(host)
        except exceptions.WebDriverException as error:
            self._exceptions.append(error)

    def _get_page_loading_time(self) -> int:
        navigation_start = self._driver.execute_script(
            "return window.performance.timing.navigationStart"
        )
        dom_complete = self._driver.execute_script(
            "return window.performance.timing.domComplete"
        )
        return dom_complete - navigation_start

    def open(
        self,
        host: str,
        timeout: int = None,
        proxy_host: Device = None,
        proxy_port: str = None,
        proxy_protocol: str = None,
        write_pcap: bool = True,
    ) -> None:
        """Main execution method.

        Args:
            host (str): destination web resource url
            timeout (int): request timeout
            proxy_host (Device): device with proxy server installed
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            proxy_protocol (str): proxy protocol, default socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        if proxy_host is not None:
            if self._singele_session_proxy is True:
                self._start_proxy(proxy_host)
            proxy_net_ifs = proxy_host.interfaces.names.pop()
            proxy_ip = proxy_host.interfaces[proxy_net_ifs].ipv4.ip.compressed
            self._set_proxy(proxy_ip, proxy_port, proxy_protocol)

        self._init_driver()

        if write_pcap is True:
            with utils.TrafficCaptureConnection(
                self._device, proxy_host=proxy_host
            ) as con:
                ip_filter = get_host_ip(host)
                con.start_capturing(filters=f"host {ip_filter}")
                self._get(host, timeout)
        else:
            self._get(host, timeout)
        if self._singele_session_proxy is True and proxy_host is not None:
            self._stop_proxy()

    def make_screenshot(self, name: str) -> None:
        self._driver.save_screenshot(f"{name}.png")

    def get_stats(self, file: str = None) -> dict:
        """Get results for post analyzis."""
        if not self._exceptions:
            loading_time = self._get_page_loading_time()
            perfornace_logs = self._driver.get_log("performance")
            browser_logs = self._driver.get_log("browser")

            stats = {
                BrowserStatKeys.LOADING_TIME: loading_time,
                BrowserStatKeys.PERF_LOGS: perfornace_logs,
                BrowserStatKeys.BROW_LOGS: browser_logs,
            }
        else:
            error = self._exceptions[0]
            stats = {BrowserStatKeys.CRIT_ERROR: error.msg}
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(json.dumps(stats))

        return stats

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._driver.quit()


class ChromeAsync(ChromeBase):
    """ChromeAsync.

    Multiple drivers Chrome session manager
    """

    def __init__(
        self, device: Device, options: list = None, single_session_proxy: bool = True
    ):
        super().__init__(device, options, single_session_proxy)
        self._drivers = []

    def _init_drivers(self, amount: int):
        """Initialize drivers."""
        self._drivers = []
        if isinstance(amount, int):
            for _ in range(amount):
                self._drivers.append(
                    webdriver.Remote(
                        command_executor=self._grid, options=self._chromeoptions
                    )
                )

    def _async_get(self, hosts: list, timeout: int):
        """Async Get.

        Asynchronously execute get methods of every driver in the
        self._drivers list with explicitly provided timeout.
        """
        if isinstance(timeout, int):
            for driver in self._drivers:
                driver.implicitly_wait(timeout)

        executor = ThreadPoolExecutor(4)
        loop = asyncio.get_event_loop()
        for index, host in enumerate(hosts):
            driver = self._drivers[index]
            loop.run_in_executor(executor, driver.get, host)
        loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks(loop)))

    def _get_page_loading_time(self, driver) -> int:
        navigation_start = driver.execute_script(
            "return window.performance.timing.navigationStart"
        )
        dom_complete = driver.execute_script(
            "return window.performance.timing.domComplete"
        )
        return dom_complete - navigation_start

    def open(
        self,
        hosts: list,
        timeout: int = None,
        proxy_host: Device = None,
        proxy_port: str = None,
        write_pcap: bool = True,
    ) -> None:
        """Main execution method.

        Args:
            hosts (list): list of destination web resources urls
            timeout (int): request timeout
            proxy_host (Device): device with proxy server installed
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        if proxy_host is not None:
            if self._singele_session_proxy is True:
                self._start_proxy(proxy_host)
            proxy_net_ifs = proxy_host.interfaces.names.pop()
            proxy_ip = proxy_host.interfaces[proxy_net_ifs].ipv4.ip.compressed
            self._set_proxy(proxy_ip, proxy_port)

        amount_of_drivers = len(hosts)
        self._init_drivers(amount_of_drivers)

        if write_pcap is True:
            with utils.TrafficCaptureConnection(
                self._device, proxy_host=proxy_host
            ) as con:
                con.start_capturing()
                self._async_get(hosts, timeout)
        else:
            self._async_get(hosts, timeout)
        if self._singele_session_proxy is True and proxy_host is not None:
            self._stop_proxy()

    def make_screenshots(self, name: str) -> None:
        for index, driver in enumerate(self._drivers):
            driver.save_screenshot(f"{name}_{index}.png")

    def get_stats(self, file: str = None) -> list:
        """Get results for post analyzis."""
        stats = []
        for driver in self._drivers:
            loading_time = self._get_page_loading_time(driver)
            perfornace_logs = driver.get_log("performance")
            browser_logs = driver.get_log("browser")

            stats.append(
                {
                    BrowserStatKeys.LOADING_TIME: loading_time,
                    BrowserStatKeys.PERF_LOGS: perfornace_logs,
                    BrowserStatKeys.BROW_LOGS: browser_logs,
                }
            )
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(json.dumps(stats))

        return stats

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for driver in self._drivers:
            driver.quit()


class Curl:
    """Curl.

    Context manager which inplements curl functionality on the remote
    device and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(self, device: Device, single_session_proxy: bool = True):
        """Constructor.

        Args:
            device (Device): device object, from where curl command will be sent
            single_session_proxy (bool): enabe proxy switching on the session level
        """
        self._device = device
        self._single_session_proxy = single_session_proxy
        self._proxy_connection = None
        self._response = None

    def _build_command(
        self,
        host: str,
        timeout: int = None,
        proxy_ip: str = None,
        proxy_port: str = None,
        proxy_protocol: str = None,
    ):
        proxy_protocol = (
            "--socks5-hostname "
            if proxy_protocol is None
            else f"--proxy {proxy_protocol}://"
        )
        proxy_port = "1080" if proxy_port is None else proxy_port

        base_command = f"curl -I {host}"
        command = base_command
        if proxy_ip is not None:
            command += f" {proxy_protocol}{proxy_ip}:{proxy_port}"
        if timeout is not None:
            command += f" --connect-timeout {timeout}"
        return command

    def _execute_command(self, command):
        self._response = self._device.curl.execute(command)

    def _start_proxy(self, proxy_host: Device):
        self._proxy_connection = Proxy(proxy_host)
        self._proxy_connection.start()

    def _stop_proxy(self):
        self._proxy_connection.stop()

    def send(
        self,
        host: str,
        timeout: int = None,
        proxy_host: Device = None,
        proxy_ip: str = None,
        proxy_port: str = None,
        proxy_protocol: str = None,
        write_pcap: bool = True,
    ) -> None:
        """Execute curl command on the device.

        Args:
            host (str): destination web resource url
            timeout (int): request timeout
            proxy_host (Device): device with proxy server installed
            proxy_ip (str): ip of the proxy host, usually not specified
            proxy_port (str): tcp port of the proxy host, 1080 is default
            proxy_protocol (str): proxy protocol, default socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        if proxy_host is not None:
            if self._singele_session_proxy is True:
                self._start_proxy(proxy_host)
            proxy_net_ifs = proxy_host.interfaces.names.pop()
            proxy_ip = (
                proxy_host.interfaces[proxy_net_ifs].ipv4.ip.compressed
                if not proxy_ip
                else proxy_ip
            )

        curl_command = self._build_command(
            host, timeout, proxy_ip, proxy_port, proxy_protocol
        )

        if write_pcap is True:
            with utils.TrafficCaptureConnection(
                self._device, proxy_host=proxy_host
            ) as con:
                ip_filter = get_host_ip(host)
                con.start_capturing(filters=f"host {ip_filter}")
                self._execute_command(curl_command)
        else:
            self._execute_command(curl_command)
        if self._singele_session_proxy is True and proxy_host is not None:
            self._stop_proxy()

    def get_response(self, file: str = None) -> str:
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(self._response)
        return self._response

    def __enter__(self):
        self._device.connect(alias="curl")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._device.curl.disconnect()


# if __name__ == "__main__":
#     from pyats.topology import loader

#     testbed = loader.load('../testbed.yaml')
#     device = testbed.devices['user-2']
#     proxy = testbed.devices['proxy-vm']

#     options = [
#         "--ignore-certificate-errors",
#         "--ignore-ssl-errors=yes"
#     ]

# # single chrome no proxy no pcap
# with Chrome(device) as chrome:
#     chrome.open(
#         host='https://tools.ietf.org:65535',
#         proxy_host=proxy,
#         write_pcap=False,
#     )
#     chrome.get_stats('A_proxy_port_65535.json')

#     # # single chrome no proxy pcap
#     # with Chrome(device) as chrome:
#     #     chrome.open(
#     #         host='https://receipt1.seiko-cybertime.jp',
#     #     )
#     #     chrome.get_stats('singlechrome_pcap_noproxy.json')

#     # # single chrome no pcap proxy
#     # with Chrome(device) as chrome:
#     #     chrome.open(
#     #         host='https://receipt1.seiko-cybertime.jp',
#     #         proxy_host=proxy,
#     #         write_pcap=False
#     #     )
#     #     chrome.get_stats('singlechrome_nopcap_proxy.json')

#     # single chrome pcap proxy
#     # with Chrome(device) as chrome:
#     #     chrome.open(
#     #         host='https://receipt1.seiko-cybertime.jp',
#     #         proxy_host=proxy,
#     #     )
#     #     chrome.get_stats('singlechrome_pcap_proxy.json')

#     # # async chrome no proxy
#     # with ChromeAsync(device) as chrome:
#     #     chrome.open(
#     #         hosts=[
#     #             "https://wiki.archlinux.org/",
#     #             "https://tools.ietf.org/html/rfc1928",
#     #             "https://docs.docker.com/"
#     #         ],
#     #         write_pcap=False
#     #     )
#     #     chrome.get_stats('asyncchrome_noproxy.json')

#     # # async chrome proxy
#     # with ChromeAsync(device) as chrome:
#     #     chrome.open(
#     #         hosts=[
#     #             "https://wiki.archlinux.org/",
#     #             "https://tools.ietf.org/html/rfc1928",
#     #             "https://dev.mysql.com/doc/refman/8.0/en/"
#     #         ],
#     #         proxy_host=proxy,
#     #         write_pcap=False,
#     #         timeout=30
#     #     )
#     #     chrome.get_stats('asyncchrome_proxy.json')
#     #     chrome.make_screenshots('async_chrome')

#     # # curl no proxy no pcap
#     # with Curl(device) as curl:
#     #     curl.send(
#     #         host='https://tools.ietf.org/html/rfc1928',
#     #         write_pcap=False
#     #     )
#     #     curl.get_response('curl_nopcap_noproxy.txt')

#     # # curl no proxy pcap
#     # with Curl(device) as curl:
#     #     curl.send(
#     #         host='https://tools.ietf.org/html/rfc1928',
#     #         write_pcap=True
#     #     )
#     #     curl.get_response('curl_pcap_noproxy.txt')

#     # # curl proxy no pcap
#     # with Curl(device) as curl:
#     #     curl.send(
#     #         host='https://httpstat.us/404',
#     #         proxy_host=proxy,
#     #         write_pcap=False
#     #     )
#     #     curl.get_response('curl_nopcap_proxy.txt')

#     # # curl proxy pcap
#     # with Curl(device) as curl:
#     #     curl.send(
#     #         host='https://httpstat.us/403',
#     #         proxy_host=proxy,
#     #         write_pcap=True
#     #     )
#     #     curl.get_response('curl_pcap_proxy.txt')
