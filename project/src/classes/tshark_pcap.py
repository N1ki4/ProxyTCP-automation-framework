import pyshark


class TsharkPcap(pyshark.FileCapture):
    """Custom class extends FileCapture class from pyshark library."""

    TEMPLATE = None

    @property
    def tcp_streams(self) -> list:
        """Return all TCP streams from the capture."""

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
    def find_packets_in_stream(self):
        """Creates list with lists of packets grouped by tcp stream.

        Specify TEMPLATE constant variable, for searching selected packets.
        """
        for stream_index in self.tcp_streams:
            self._display_filter = f"tcp.stream == {stream_index}"
            if self.TEMPLATE.issubset(set(self.tls_data)):
                return "Packets in stream were found."
        return "No selected packets were found."
