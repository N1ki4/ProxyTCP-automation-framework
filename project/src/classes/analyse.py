import re

from src.classes.clients import BrowserStats


class BrowserResponseAnalyzer:
    """Analyse browser response."""

    _target_method = "Network.responseReceived"
    _fail_method = "Network.loadingFailed"
    _content_type = ("text/html", "text/plain")

    def __init__(self, response: dict):
        self._response = response
        self._loading_time = response.get(BrowserStats.LOADING_TIME)
        self._performance_logs = response.get(BrowserStats.PERF_LOGS)
        self._browser_logs = response.get(BrowserStats.BROW_LOGS)
        self._critical_error = response.get(BrowserStats.CRIT_ERROR)

        # get targeted entries of performance logs
        self._recieved_content = (
            list(
                filter(
                    lambda x: x["message"]["message"]["method"] == self._target_method,
                    self._performance_logs,
                )
            )
            if self._performance_logs
            else None
        )

    def get_loading_time(self) -> float:
        if not self._critical_error:
            return self._loading_time / 1000

    def get_status_code(self) -> int:
        if not self._critical_error:
            find_in_response = list(
                filter(
                    lambda x: x["message"]["message"]["params"]["response"]["mimeType"]
                    in self._content_type,
                    self._recieved_content,
                )
            )[0]
            return find_in_response["message"]["message"]["params"]["response"][
                "status"
            ]

    def get_remote_ip_port(self) -> tuple:
        if not self._critical_error:
            find_in_response = list(
                filter(
                    lambda x: x["message"]["message"]["params"]["response"]["mimeType"]
                    in self._content_type,
                    self._recieved_content,
                )
            )[0]
            ip = find_in_response["message"]["message"]["params"]["response"][
                "remoteIPAddress"
            ]
            port = find_in_response["message"]["message"]["params"]["response"][
                "remotePort"
            ]
            return ip, port

    def get_browser_errors(self) -> list:
        result = []
        if not self._critical_error:
            find_in_performance_logs = list(
                filter(
                    lambda x: x["message"]["message"]["method"] == self._fail_method,
                    self._performance_logs,
                )
            )
            find_in_browser_logs = list(
                filter(
                    lambda x: x["level"] in ("SEVERE", "WARNING"), self._browser_logs
                )
            )
            find_in_response = find_in_performance_logs + find_in_browser_logs
            for entry in find_in_response:
                result.append(str(entry["message"]))
        else:
            result.append(self._critical_error)
        return result

    def get_requests_statistics(self) -> int:
        request_sent_pattern = "\\bNetwork.requestWillBeSent\\b"
        return len([*re.finditer(request_sent_pattern, str(self._response))])

    def get_response_statistics(self) -> int:
        response_received_pattern = "\\bNetwork.responseReceived\\b"
        return len([*re.finditer(response_received_pattern, str(self._response))])

    def get_loading_failed_statistics(self) -> int:
        response_received_pattern = "\\bNetwork.loadingFailed\\b"
        return len([*re.finditer(response_received_pattern, str(self._response))])


class CurlResponseAnalyzer:
    """Analyse curl response."""

    def __init__(self, response: str):
        self._response = response

    def get_status_code(self) -> int:
        pattern = r"HTTP/(\d|(\d\.\d))\s(\d+)"
        result = re.compile(pattern).search(self._response)
        if result is not None:
            return int(result[3])
