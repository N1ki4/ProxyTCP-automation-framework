# pylint: disable=no-self-use # pyATS-related exclusion
# pylint: disable=attribute-defined-outside-init # pyATS-related exclusion
import os
import logging


from pyats import aetest


from src.classes.remote_tools import SeleniumGrid
from src.classes.clients import Chrome, Curl
from src.classes.tshark_pcap import TsharkPcap
from src.classes.utils import _temp_files_dir
from src.classes.analyse import CurlResponseAnalyzer


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
        grid.start()


class SocksHandshakeSuccess(aetest.Testcase):
    @aetest.test
    def test_socks_handshake(self, user, proxy, host):

        with Chrome(grid_server=user, proxy_server=proxy, traffic_dump=True) as chrome:
            chrome.get(host)

        pcap_file = f"{user.name}_tshark.pcap"
        pcap_file = os.path.join(_temp_files_dir, pcap_file)
        pcap_obj = TsharkPcap(pcap_file)

        if pcap_obj.find_packets_in_stream(packet_type="socks")[0] is False:
            self.failed("Socks 5 handshake sequence not found")


class StatusCodesCorrectTransfer(aetest.Testcase):
    @aetest.setup
    def setup_loop(self):
        aetest.loop.mark(
            self.test_code, host=self.parameters["hosts"], code=self.parameters["codes"]
        )

    @aetest.test
    def test_code(self, user, proxy, host, code):

        with Curl(client_server=user, proxy_server=proxy, session_timeout=10) as curl:
            curl.get(host)
            stats = curl.get_response()

        data = CurlResponseAnalyzer(stats)
        status_code = data.get_status_code()
        if status_code != code:
            self.failed(f"Expected status code {code}, got {status_code}")


class HTTPNotSupported(aetest.Testcase):
    @aetest.test
    def connect_http(self, user, proxy, host):

        with Curl(client_server=user, proxy_server=proxy, session_timeout=10) as curl:
            curl.get(host)
            stats = curl.get_response()

        if "Operation timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class FTPNotSupported(aetest.Testcase):
    @aetest.test
    def connect_http(self, user, proxy, host):

        with Curl(client_server=user, proxy_server=proxy, session_timeout=10) as curl:
            curl.get(host)
            stats = curl.get_response()

        if "Operation timed out" not in stats:
            self.failed(f"Expected connection timeout, got {stats}")


class IncorrectProxyProtocol(aetest.Testcase):
    @aetest.test
    def incorrect_protocol_test(self, user, proxy, host, protocol):

        with Curl(
            client_server=user,
            proxy_server=proxy,
            session_timeout=10,
            proxy_protocol=protocol,
        ) as curl:
            curl.get(host)
            stats = curl.get_response()

        if "Failed to receive SOCKS4 connect request ack" not in stats:
            self.failed(
                f"Expected `Failed to receive SOCKS4 connect request ack`, got {stats}"
            )


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
