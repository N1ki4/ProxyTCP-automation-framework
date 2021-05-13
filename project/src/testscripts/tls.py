# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import os


from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.tshark_pcap import TsharkPcap
from src.classes.utils import _temp_files_dir
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


class BrockenCerts(aetest.Testcase):

    parameters = {"host": "https://www.grupoemsa.org/"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def brocken_certs_test(self, host):
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
        errors = data.get_browser_errors()
        pass_condition = len(errors) >= 1 and "ERR_CERT_AUTHORITY_INVALID" in errors[0]
        if not pass_condition:
            self.failed("Invalod response, no `ERR_CERT_AUTHORITY_INVALID` occured!")


class ObsoleteTLS(aetest.Testcase):

    parameters = {"host": "https://receipt1.seiko-cybertime.jp"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def obsolete_tls_test(self, host):
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
        errors = data.get_browser_errors()
        print(errors)
        expected_message = (
            f"The connection used to load resources from {host}"
            " used TLS 1.0 or TLS 1.1, which are deprecated and will be disabled"
            " in the future."
        )
        pass_condition = False
        if errors:
            for error in errors:
                if expected_message in error:
                    pass_condition = True
        if not pass_condition:
            self.failed("Invalod response, no `ERR_SSL_OBSOLETE_VERSION` occured!")


class TLSHandshake12(aetest.Testcase):

    parameters = {"host": "https://tools.ietf.org/html/rfc5246"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def tls_1_2_handshake_test(self, host):
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

        if pcap_obj.find_packets_in_stream(packet_type="tls1.2")[0] is False:
            self.failed("TLS handshake sequence not found")


class TLSHandshake13(aetest.Testcase):

    parameters = {"host": "https://en.wikipedia.org/wiki/Internet_Protocol"}

    @aetest.setup
    def setup(self, testbed):
        self.proxy_device = testbed.devices["proxy-vm"]
        self.user_device = testbed.devices["user-1"]

    @aetest.test
    def tls_1_3_handshake_test(self, host):
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

        if pcap_obj.find_packets_in_stream(packet_type="tls1.3")[0] is False:
            self.failed("TLS handshake sequence not found")


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
    logging.getLogger("unicon").setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--testbed", dest="testbed", type=topology.loader.load)

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(testbed=args.testbed)
