# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
import re
import json
import asyncio
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from abc import ABC
from typing import Union

from selenium import webdriver
from selenium.common import exceptions
from pyats.topology import Device

from src.classes.utils import TrafficDump
from src.classes.sut import Proxy


_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)


class BrowserStats:
    """Browser response data toolbox."""

    LOADING_TIME = "loading_time"
    PERF_LOGS = "performance_logs"
    BROW_LOGS = "browser_logs"
    CRIT_ERROR = "critical_error"

    @staticmethod
    def serializer(response: Union[list, dict]) -> Union[list, dict]:
        """Serialize browser response data."""
        key = BrowserStats.PERF_LOGS

        if isinstance(response, list):
            for entry in response:
                for index, _ in enumerate(entry[key]):
                    entry[key][index]["message"] = json.loads(
                        entry[key][index]["message"]
                    )

        elif isinstance(response, dict) and "critical_error" not in response.keys():
            for index, _ in enumerate(response[key]):
                response[key][index]["message"] = json.loads(
                    response[key][index]["message"]
                )
        return response

    def __str__(self):
        return f"{self.LOADING_TIME}, {self.PERF_LOGS}, {self.BROW_LOGS}, {self.CRIT_ERROR}"


class ChromeBase(ABC):
    """ChromeBase.

    Context manager which inplements selenium chrome functionality
    and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(
        self,
        grid_server: Device,
        session_timeout: int,
        chrome_arguments: list,
        proxy_server: Device,
        proxy_protocol: str,
        proxy_ip: str,
        proxy_port: str,
        session_wide_proxy: bool,
        traffic_dump: bool,
        unicon_log: str,
    ):
        """Constructor.

        Args:
            grid_server (Device): server, from where selenium traffic will be generated
            chrome_arguments (list): chrome as command line arguments
            session_timeout (int): webdriver session timeout
            proxy_server (Device): proxy hosting server
            proxy_protocol (str): proxy protocol
            proxy_ip (str): proxy ip
            proxy_port (str): proxy port
            session_wide_proxy (bool): enabe proxy switching on the session level
            (if proxy is defined)
            traffic_dump (str): enable traffic recording via tshark
            unicon_log (str): file for unicon module logs
        """

        self._grid_server = grid_server
        self._session_timeout = session_timeout
        self._chromeoptions = None
        self._grid = None
        self._proxy_enabled = False
        self._proxy_controller = None
        self._tshark_contrller = None
        self._exceptions = []
        self._loghead = f"Chrome@{grid_server.name}"

        # apply options
        chromeoptions = webdriver.ChromeOptions()
        if isinstance(chrome_arguments, list):
            for entry in chrome_arguments:
                chromeoptions.add_argument(entry)
        self._chromeoptions = chromeoptions

        # set proxy
        if isinstance(proxy_server, Device):
            if not proxy_ip:
                proxy_net_ifs = proxy_server.interfaces.names.pop()
                proxy_ip = proxy_server.interfaces[proxy_net_ifs].ipv4.ip.compressed
            proxy_protocol = "socks5" if proxy_protocol is None else proxy_protocol
            proxy_port = "1080" if proxy_port is None else proxy_port
            option = f"--proxy-server={proxy_protocol}://{proxy_ip}:{proxy_port}"
            self._chromeoptions.add_argument(option)
            self._proxy_enabled = True

            if session_wide_proxy is True:
                self._proxy_controller = Proxy(proxy_server, logfile=unicon_log)

        # enable webdriver logs collection
        self._chromeoptions.capabilities["goog:loggingPrefs"] = {
            "performance": "ALL",
            "browser": "ALL",
        }

        # identify selenium grid
        connection = self._grid_server.connections.cli.command
        host = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[3]
        grid = f"http://{host}:4444/wd/hub"
        self._grid = grid

        # initialize tshark
        if traffic_dump is True:
            self._tshark_contrller = TrafficDump(
                grid_server, proxy_server, logfile=unicon_log
            )

    def __enter__(self):
        if isinstance(self._proxy_controller, Proxy):
            self._proxy_controller.start()
        if isinstance(self._tshark_contrller, TrafficDump):
            self._tshark_contrller.start_capturing()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(self._tshark_contrller, TrafficDump):
            self._tshark_contrller.stop_capturing()
        if isinstance(self._proxy_controller, Proxy):
            self._proxy_controller.stop()


class Chrome(ChromeBase):
    """Chrome.

    Single driver Chrome session manager.
    """

    def __init__(
        self,
        grid_server: Device,
        session_timeout: int = 30,
        chrome_arguments: list = None,
        proxy_server: Device = None,
        proxy_protocol: str = None,
        proxy_ip: str = None,
        proxy_port: str = None,
        session_wide_proxy: bool = True,
        traffic_dump: bool = False,
        unicon_log: str = None,
    ):
        super().__init__(
            grid_server,
            session_timeout,
            chrome_arguments,
            proxy_server,
            proxy_protocol,
            proxy_ip,
            proxy_port,
            session_wide_proxy,
            traffic_dump,
            unicon_log,
        )
        self._driver = None

        # initialize driver
        self._driver = webdriver.Remote(
            command_executor=self._grid, options=self._chromeoptions
        )
        if isinstance(self._session_timeout, int):
            self._driver.implicitly_wait(self._session_timeout)

    @property
    def driver(self) -> webdriver.Remote:
        return self._driver

    def get(self, host: str) -> None:
        _log.info(f"{self._loghead} - get URL: {host}")
        try:
            self._driver.get(host)
            _log.info(f"{self._loghead} - loading complete")
        except exceptions.WebDriverException as error:
            self._exceptions.append(error)

    def refresh(self) -> None:
        _log.info(f"{self._loghead} - reloading webpage")
        self._driver.refresh()
        _log.info(f"{self._loghead} - loading complete")

    def get_stats(self, write_to_file: str = None) -> dict:
        """Get results for post analyzis."""
        stats = {}
        if not self._exceptions:
            loading_time = self._get_page_loading_time()
            perfornace_logs = self._driver.get_log("performance")
            browser_logs = self._driver.get_log("browser")

            stats = {
                BrowserStats.LOADING_TIME: loading_time,
                BrowserStats.PERF_LOGS: perfornace_logs,
                BrowserStats.BROW_LOGS: browser_logs,
            }
        else:
            error = self._exceptions[0]
            stats = {BrowserStats.CRIT_ERROR: error.msg}
        data = BrowserStats.serializer(stats)
        if isinstance(write_to_file, str):
            with open(write_to_file, "w") as f:
                f.write(json.dumps(data))

        return data

    def make_screenshot(self, name: str) -> None:
        self._driver.save_screenshot(f"{name}.png")

    def _get_page_loading_time(self) -> int:
        navigation_start = self._driver.execute_script(
            "return window.performance.timing.navigationStart"
        )
        dom_complete = self._driver.execute_script(
            "return window.performance.timing.domComplete"
        )
        return dom_complete - navigation_start

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        self._driver.quit()


class ChromeAsync(ChromeBase):
    """ChromeAsync.

    Multiple drivers Chrome session manager
    """

    def __init__(
        self,
        grid_server: Device,
        max_num_of_instances: int = 4,
        session_timeout: int = 30,
        chrome_arguments: list = None,
        proxy_server: Device = None,
        proxy_protocol: str = None,
        proxy_ip: str = None,
        proxy_port: str = None,
        session_wide_proxy: bool = True,
        traffic_dump: bool = False,
        unicon_log: str = None,
    ):
        super().__init__(
            grid_server,
            session_timeout,
            chrome_arguments,
            proxy_server,
            proxy_protocol,
            proxy_ip,
            proxy_port,
            session_wide_proxy,
            traffic_dump,
            unicon_log,
        )
        self._max_num_of_instances = max_num_of_instances
        self._drivers = []

        # initialize drivers
        for _ in range(max_num_of_instances):
            driver = webdriver.Remote(
                command_executor=self._grid, options=self._chromeoptions
            )
            if isinstance(self._session_timeout, int):
                driver.implicitly_wait(self._session_timeout)
            self._drivers.append(driver)

    def get(self, hosts: list):
        """Get.

        Asynchronously execute get methods of every driver in the
        self._drivers list with explicitly provided timeout.
        """
        executor = ThreadPoolExecutor(self._max_num_of_instances)
        loop = asyncio.get_event_loop()
        for index, host in enumerate(hosts):
            driver = self._drivers[index]
            _log.info(f"{self._loghead} - get URL: {host}")
            loop.run_in_executor(executor, driver.get, host)
        loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks(loop)))
        _log.info(f"{self._loghead} - loading complete: {len(hosts)} pages loaded")

    def make_screenshots(self, name: str) -> None:
        for index, driver in enumerate(self._drivers):
            if driver.session_id is not None:
                driver.save_screenshot(f"{name}_{index}.png")

    def get_stats(self, write_to_file: str = None) -> list:
        """Get results for post analyzis."""
        stats = []
        for driver in self._drivers:
            loading_time = self._get_page_loading_time(driver)
            perfornace_logs = driver.get_log("performance")
            browser_logs = driver.get_log("browser")

            stats.append(
                {
                    BrowserStats.LOADING_TIME: loading_time,
                    BrowserStats.PERF_LOGS: perfornace_logs,
                    BrowserStats.BROW_LOGS: browser_logs,
                }
            )
        data = BrowserStats.serializer(stats)
        if isinstance(write_to_file, str):
            with open(write_to_file, "w") as f:
                f.write(json.dumps(data))

        return data

    @staticmethod
    def _get_page_loading_time(driver) -> int:
        navigation_start = driver.execute_script(
            "return window.performance.timing.navigationStart"
        )
        dom_complete = driver.execute_script(
            "return window.performance.timing.domComplete"
        )
        return dom_complete - navigation_start

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        for driver in self._drivers:
            driver.quit()


class Curl:
    """Curl.

    Context manager which inplements curl functionality on the remote
    device and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(
        self,
        client_server: Device,
        session_timeout: int = 30,
        proxy_server: Device = None,
        proxy_protocol: str = None,
        proxy_ip: str = None,
        proxy_port: str = None,
        session_wide_proxy: bool = True,
        traffic_dump: bool = False,
        unicon_log: str = None,
    ):
        """Constructor.

        Args:
            client_server (Device): server, from where curl request will be sent
            session_timeout (int): curl response timeout
            proxy_server (Device): proxy hosting server
            proxy_protocol (str): proxy protocol
            proxy_ip (str): proxy ip
            proxy_port (str): proxy port
            session_wide_proxy (bool): enabe proxy switching on the session level
            (if proxy is defined)
            traffic_dump (str): enable traffic recording via tshark
            unicon_log (str): file for unicon module logs
        """
        self._client_server = client_server
        self._session_timeout = session_timeout
        self._unicon_log = unicon_log
        self._base_command = "curl -I "
        self._command_args = ""
        self._proxy_enabled = False
        self._proxy_controller = None
        self._tshark_contrller = None
        self._response = None
        self._loghead = f"CURL@{client_server.name}"

        # set proxy
        if isinstance(proxy_server, Device):
            if not proxy_ip:
                proxy_net_ifs = proxy_server.interfaces.names.pop()
                proxy_ip = proxy_server.interfaces[proxy_net_ifs].ipv4.ip.compressed
            proxy_protocol = (
                " --socks5-hostname "
                if proxy_protocol is None
                else f" --proxy {proxy_protocol}://"
            )
            proxy_port = "1080" if proxy_port is None else proxy_port
            self._command_args += f"{proxy_protocol}{proxy_ip}:{proxy_port}"
            self._proxy_enabled = True

            if session_wide_proxy is True:
                self._proxy_controller = Proxy(proxy_server)

        # set timeout
        if isinstance(session_timeout, int):
            self._command_args += f" --max-time {session_timeout}"

        # initialize tshark
        if traffic_dump is True:
            self._tshark_contrller = TrafficDump(client_server, proxy_server)

    def get(self, host: str) -> None:
        command = self._base_command + host + self._command_args
        _log.info(f"{self._loghead} - executing command: {command}")
        self._response = self._client_server.curl.execute(command)
        _log.info(f"{self._loghead} - response recieved: {self._response}")

    def get_response(self, file: str = None) -> str:
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(self._response)
        return self._response

    def __enter__(self):
        self._client_server.connect(alias="curl", logfile=self._unicon_log)
        if isinstance(self._proxy_controller, Proxy):
            self._proxy_controller.start()
        if isinstance(self._tshark_contrller, TrafficDump):
            self._tshark_contrller.start_capturing()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(self._tshark_contrller, TrafficDump):
            self._tshark_contrller.stop_capturing()
        if isinstance(self._proxy_controller, Proxy):
            self._proxy_controller.stop()
        self._client_server.curl.disconnect()


# if __name__ == "__main__":
#     from pyats.topology import loader

#     testbed = loader.load('../testbed.yaml')
#     device = testbed.devices['user-2']
#     proxy = testbed.devices['proxy-vm']


# with Chrome(grid_server=device) as chrome:
#     chrome.get(host='https://tools.ietf.org')
#     chrome.get_stats('B_noproxy_nopcap.json')

# with Chrome(grid_server=device, proxy_server=proxy) as chrome:
#     chrome.get(host='https://tools.ietf.org')
#     chrome.get_stats('B_proxy_nopcap.json')
#     chrome.make_screenshot('B_proxy_nopcap')

# with Chrome(grid_server=device, traffic_dump=True) as chrome:
#     chrome.get(host='https://tools.ietf.org')
#     chrome.get_stats('B_noproxy_pcap.json')
#     chrome.make_screenshot('B_noproxy_nopcap')

# with Chrome(grid_server=device, proxy_server=proxy, traffic_dump=True) as chrome:
#     chrome.get(host='https://tools.ietf.org')
#     chrome.get_stats('B_proxy_pcap.json')
#     chrome.make_screenshot('B_proxy_nopcap')
