import re
import json
import socket
import logging
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from abc import ABC

from selenium import webdriver
from pyats.topology import Device, Testbed

from src.classes import utils


logging.getLogger("unicon").setLevel(logging.ERROR)


def get_host_ip(host) -> str:
    """Retrieve IP of the host to set capture filters in tshark."""
    host = re.compile(r"(http|https)://((\w+\.)+\w+)").search(host)[2]
    return socket.gethostbyname(host)


class ChromeBase(ABC):
    """ChromeBase.

    Context manager which inplements chrome functionality
    and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(self, testbed: Testbed, device: Device, options: list, pcap_file: str):
        """Constructor.

        Args:
            testbed (Tesbed): testbed object
            device (Device): device object, which grid will be triggered
            options (list): options for chrome as command line arguments
            pcap_file (str): file on the device where to store traffic capture
        """

        self._device = device

        # default network interface of the device
        self._interface = device.interfaces.names.pop()

        # filemanger for copying files from the device to the testing host
        self._fileutils = utils.FileUtils(testbed, device)

        self._chromeoptions = None
        self._grid = None
        self._proxy_enabled = False
        self._pcapfile = "tshark.pcap" if pcap_file is None else pcap_file

        # apply options
        chromeoptions = webdriver.ChromeOptions()
        if isinstance(options, list):
            for entry in options:
                chromeoptions.add_argument(entry)
        self._chromeoptions = chromeoptions

        # enable logging
        self._chromeoptions.capabilities["goog:loggingPrefs"] = {
            "performance": "ALL",
            "browser": "ALL",
        }

        # identify selenium grid
        connection = self._device.connections.cli.command
        host = re.compile(r"ssh -i (/.*)+\s(\w+)@(.*)").search(connection)[3]
        grid = f"http://{host}:4444/wd/hub"
        self._grid = grid

    def _set_proxy(self, proxy_host: str, proxy_port: str = "1080") -> None:
        """Set proxy servere parameters.

        Args:
            proxy_host (str): ip address of the proxy host
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
        """
        option = f"--proxy-server=socks5://{proxy_host}:{proxy_port}"
        self._add_option(option)
        self._proxy_enabled = True

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
        self,
        testbed: Testbed,
        device: Device,
        options: list = None,
        pcap_file: str = None,
    ):
        super().__init__(testbed, device, options, pcap_file)
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
        self._driver.get(host)

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
        proxy_host: str = None,
        proxy_port: str = None,
        write_pcap: bool = True,
    ) -> None:
        """Main execution method.

        Args:
            host (str): destination web resource url
            timeout (int): request timeout
            proxy_host (str): ip address of the proxy host
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        if proxy_host is not None and proxy_port is not None:
            self._set_proxy(proxy_host, proxy_port)

        self._init_driver()

        if write_pcap is True:
            with utils.DumpCon(self._device) as con:
                ip_filter = get_host_ip(host) if not self._proxy_enabled else proxy_host
                con.start_tshark(
                    interface=self._interface,
                    filters=f"host {ip_filter}",
                    capfile=self._pcapfile,
                )
                self._get(host, timeout)
        else:
            self._get(host, timeout)

    def make_screenshot(self, name: str) -> None:
        self._driver.save_screenshot(f"{name}.png")

    def get_stats(self, file: str = None) -> dict:
        """Get results for post analyzis."""
        loading_time = self._get_page_loading_time()
        perfornace_logs = self._driver.get_log("performance")
        browser_logs = self._driver.get_log("browser")

        stats = {
            "loading_time": loading_time,
            "performance_logs": perfornace_logs,
            "browser_logs": browser_logs,
        }
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(json.dumps(stats))

        return stats

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._driver.quit()
        self._fileutils.copy_from_device(source=self._pcapfile)
        self._fileutils.copy_from_device(source=self._pcapfile)


class ChromeAsync(ChromeBase):
    """ChromeAsync.

    Multiple drivers Chrome session manager
    """

    def __init__(
        self,
        testbed: Testbed,
        device: Device,
        options: list = None,
        pcap_file: str = None,
    ):
        super().__init__(testbed, device, options, pcap_file)
        self._drivers = []

    def _init_drivers(self, amount: int):
        """Initialize drivers."""
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
        proxy_host: str = None,
        proxy_port: str = None,
        write_pcap: bool = True,
    ) -> None:
        """Main execution method.

        Args:
            hosts (list): list of destination web resources urls
            timeout (int): request timeout
            proxy_host (str): ip address of the proxy host
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        if proxy_host is not None and proxy_port is not None:
            self._set_proxy(proxy_host, proxy_port)

        amount_of_drivers = len(hosts)
        self._init_drivers(amount_of_drivers)

        if write_pcap is True:
            with utils.DumpCon(self._device) as con:
                con.start_tshark(
                    interface=self._interface,
                    capfile=self._pcapfile,
                )
                self._async_get(hosts, timeout)
        else:
            self._async_get(hosts, timeout)

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
                    "loading_time": loading_time,
                    "performance_logs": perfornace_logs,
                    "browser_logs": browser_logs,
                }
            )
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(json.dumps(stats))

        return stats

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for driver in self._drivers:
            driver.quit()
        self._fileutils.copy_from_device(source=self._pcapfile)
        self._fileutils.copy_from_device(source=self._pcapfile)


class Curl:
    """Curl.

    Context manager which inplements curl functionality on the remote
    device and combine it with pcap writing and sending them back to
    the testing host for the analysis.
    """

    def __init__(self, testbed: Testbed, device: Device, datafiles: dict = None):
        """Constructor.

        Args:
            testbed (Tesbed): testbed object
            device (Device): device object, which grid will be triggered
            datafiles (dict): path to curl and pcap files on the device
        """
        self._device = device
        self._fileutils = utils.FileUtils(testbed, device)
        self._datafiles = (
            {"curl_file": "curl.txt", "pcap_file": "tshark.pcap"}
            if datafiles is None
            else datafiles
        )

    def _build_command(
        self,
        host: str,
        timeout: int = None,
        proxy_host: str = None,
        proxy_port: str = None,
    ):
        base_command = f"curl {host}"
        command = base_command
        if proxy_host is not None and proxy_port is not None:
            command += f" --socks5-hostname {proxy_host}:{proxy_port}"
        if timeout is not None:
            command += f" --connect-timeout {timeout}"
        command += f' > {self._datafiles["curl_file"]}'
        return command

    def send(
        self,
        host: str,
        timeout: int = None,
        proxy_host: str = None,
        proxy_port: str = None,
        write_pcap: bool = False,
    ) -> None:
        """Execute curl command on the device.

        Args:
            host (str): destination web resource url
            timeout (int): request timeout
            proxy_host (str): ip address of the proxy host
            proxy_port (str): tcp port of the proxy host, 1080 is default for socks5
            write_pcap (bool): capture traffic with tshark and write to file
        """

        curl_command = self._build_command(host, timeout, proxy_host, proxy_port)

        with utils.DumpCon(self._device) as con:
            if write_pcap is True:
                ip_filter = get_host_ip(host) if not proxy_host else proxy_host
                con.start_tshark(
                    filters=f"host {ip_filter}",
                    capfile=self._datafiles["pcap_file"],
                )
            con.device.execute(curl_command + "&& echo -ne '\n'")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._fileutils.copy_from_device(source=self._datafiles["curl_file"])
        self._fileutils.copy_from_device(source=self._datafiles["pcap_file"])
