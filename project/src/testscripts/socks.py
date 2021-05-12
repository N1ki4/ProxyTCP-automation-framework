# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import os


from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, Curl
from src.classes.tshark_pcap import TsharkPcap
from src.classes.utils import _temp_files_dir
from src.classes.analyse import (
    CurlResponseAnalyzer,
)


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def start_selenium(self, testbed):
        user_device = testbed.devices["user-1"]
        grid = SeleniumGrid(user_device)
        grid.start()


class SocksHandshakeSuccess(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org/"}

    @aetest.setup
    def start_services(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def test_socks_handshake(self, host):
        with Chrome(self.user_device) as chrome:
            chrome.open(
                host=host,
                proxy_host=self.proxy_device,
                timeout=30,
                write_pcap=True,
            )
        pcap_file = f"{self.user_device.name}_tshark.pcap"
        pcap_file = os.path.join(_temp_files_dir, pcap_file)
        pcap_obj = TsharkPcap(pcap_file)

        if pcap_obj.find_packets_in_stream(packet_type="socks")[0] is False:
            self.failed("Socks 5 handshake sequence not found")


class StatusCodesCorrectTransfer(aetest.Testcase):

    parameters = {
        "hosts": [
            "https://httpstat.us/200",
            "https://httpstat.us/301",
            "https://httpstat.us/400",
            "https://httpstat.us/403",
            "https://httpstat.us/404",
            "https://httpstat.us/500",
            "https://httpstat.us/502",
            "https://httpstat.us/503",
        ],
        "codes": [200, 301, 400, 403, 404, 500, 502, 503],
    }

    @aetest.setup
    def start_services(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

        aetest.loop.mark(
            self.test_code, host=self.parameters["hosts"], code=self.parameters["codes"]
        )

    @aetest.test
    def test_code(self, host, code):
        with Curl(self.user_device) as curl:
            curl.send(
                host=host, proxy_host=self.proxy_device, timeout=10, write_pcap=False
            )
            stats = curl.get_response("curl_pcap_proxy.txt")
        data = CurlResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != code:
            self.failed(f"Expected status code {code}, got {status_code}")


class HTTPNotSupported(aetest.Testcase):

    parameters = {"host": "http://lutasprava.com"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def connect_http(self, host):
        with Curl(self.user_device) as curl:
            curl.send(
                host=host,
                proxy_host=self.proxy_device,
                timeout=10,
                write_pcap=False,
            )
            stats = curl.get_response("curl_pcap_proxy.txt")
        if "Connection timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class FTPNotSupported(aetest.Testcase):

    parameters = {"host": "ftp://speedtest.tele2.net/"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def connect_ftp(self, host):
        with Curl(self.user_device) as curl:
            curl.send(
                host=host,
                proxy_host=self.proxy_device,
                timeout=10,
                write_pcap=False,
            )
            stats = curl.get_response("curl_pcap_proxy.txt")
        if "Connection timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class IncorrectProxyProtocol(aetest.Testcase):

    parameters = {"host": "https://wiki.archlinux.org/ ", "protocol": "socks4"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def incorrect_protocol_test(self, host, protocol):
        with Curl(self.user_device) as curl:
            curl.send(
                host=host,
                proxy_host=self.proxy_device,
                proxy_protocol=protocol,
                timeout=10,
                write_pcap=False,
            )
            stats = curl.get_response("curl_pcap_proxy.txt")
        if "Connection timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


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
