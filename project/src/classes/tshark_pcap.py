# pylint: disable=cell-var-from-loop
import pyshark


class TsharkPcap(pyshark.FileCapture):
    """Custom class extends FileCapture class from pyshark library."""

    _tls_handshake_tmplate = None
    _socks_handshake_template = {
        "connect to server request": {
            "payload": "05:01:00",
            "min length": 3,
            "max length": 3,
        },
        "connect to server response": {
            "payload": "05:00",
            "min length": 2,
            "max length": 2,
        },
        "command request - connect": {
            "payload": "05:01",
            "min length": 4,
            "max length": 100,
        },
        "command response - connect": {
            "payload": "05:00",
            "min length": 4,
            "max length": 100,
        },
    }

    @property
    def tcp_streams(self) -> list:
        """Return TCP streams with payload."""

        seen_index = []
        for packet in self:
            try:
                seen_index.append(packet.tcp.stream)
            except AttributeError:
                continue
        return [int(x) for x in list(set(seen_index))]

    @property
    def tls_data(self) -> list:
        """Extract all TLS records from capturing as list."""
        tls_packets = []
        for packet in self:
            try:
                if packet.tls:
                    tls_packets.append(packet.tls._all_fields["tls.record"])
            except AttributeError:
                continue
        return tls_packets

    @property
    def tcp_data(self) -> list:
        """Extract all TCP records from capturing as list."""
        tcp_packets = []
        for packet in self:
            try:
                if packet.tcp._all_fields.get("tcp.payload") is not None:
                    tcp_packets.append(packet.tcp)
            except AttributeError:
                continue
        return tcp_packets

    def find_packets_in_stream(self, packet_type: str):
        """Creates list with lists of packets grouped by tcp stream."""

        if packet_type.lower() == "tls":
            for stream_index in self.tcp_streams:
                self._display_filter = f"tcp.stream == {stream_index}"
                if self._tls_handshake_tmplate.issubset(set(self.tls_data)):
                    return "Packets in stream were found."
            return "No selected packets were found."

        # find socks handshake packets
        if packet_type.lower() == "socks":
            pass_condition = False
            content = {}

            # look for socks handshake in each tcp stream
            for stream_index in self.tcp_streams:
                packet_found = []
                self._display_filter = f"tcp.stream == {stream_index}"

                for template in self._socks_handshake_template.values():
                    found = list(
                        filter(
                            lambda x: template["payload"]
                            in x._all_fields.get("tcp.payload")
                            and (
                                int(x._all_fields.get("tcp.len"))
                                >= template["min length"]
                            )
                            and (
                                int(x._all_fields.get("tcp.len"))
                                <= template["max length"]
                            ),
                            self.tcp_data,
                        )
                    )
                    if len(found) >= 1:
                        packet_found.append(found[0])

                # if all 4 handshake entries were found in a single stream, terminate cycle and
                # return results
                if len(packet_found) == 4:
                    pass_condition = True
                    content = {
                        "stream index": stream_index,
                        "handshake payload": [
                            i._all_fields.get("tcp.payload") for i in packet_found
                        ],
                    }
                    break
            return pass_condition, content


if __name__ == "__main__":
    cap = TsharkPcap("/pyats/project/src/temp/user-2_tshark.pcap")
    res = cap.find_packets_in_stream(packet_type="socks")
