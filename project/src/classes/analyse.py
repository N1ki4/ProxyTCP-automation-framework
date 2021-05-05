import re
import json
from typing import Union


class BrowserStatKeys:
    """Response keys."""

    LOADING_TIME = "loading_time"
    PERF_LOGS = "performance_logs"
    BROW_LOGS = "browser_logs"
    CRIT_ERROR = "critical_error"


def serializer(response: Union[list, dict]) -> Union[list, dict]:
    """Serialize response data."""
    key = BrowserStatKeys.PERF_LOGS

    if isinstance(response, list):
        for entry in response:
            for index, _ in enumerate(entry[key]):
                entry[key][index]["message"] = json.loads(entry[key][index]["message"])

    elif isinstance(response, dict) and "critical_error" not in response.keys():
        for index, _ in enumerate(response[key]):
            response[key][index]["message"] = json.loads(
                response[key][index]["message"]
            )

    return response


class BrowserResponseAnalyzer:
    """Analyse browser response."""

    _target_method = "Network.responseReceived"
    _content_type = ("text/html", "text/plain")

    def __init__(self, response: dict):
        self._response = response
        self._loading_time = response.get(BrowserStatKeys.LOADING_TIME)
        self._performance_logs = response.get(BrowserStatKeys.PERF_LOGS)
        self._browser_logs = response.get(BrowserStatKeys.BROW_LOGS)
        self._critical_error = response.get(BrowserStatKeys.CRIT_ERROR)

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
            find_in_response = list(
                filter(
                    lambda x: x["level"] in ("SEVERE", "WARNING"), self._browser_logs
                )
            )
            for entry in find_in_response:
                result.append(entry["message"])
        else:
            result.append(self._critical_error)
        return result

    def get_requests_statistics(self) -> tuple:
        request_sent_pattern = "\\bNetwork.requestWillBeSent\\b"
        response_recieved_pattern = "\\bNetwork.responseReceived\\b"
        loading_failed_pattern = "\\bNetwork.loadingFailed\\b"

        sent = len([*re.finditer(request_sent_pattern, str(self._response))])
        recieved = len([*re.finditer(response_recieved_pattern, str(self._response))])
        failed = len([*re.finditer(loading_failed_pattern, str(self._response))])

        return sent, recieved, failed

    @staticmethod
    def count_average(stats) -> bool:
        requests_with_proxy = list(
            (request["requestWillBeSent"]) for request in stats[: int(len(stats) / 2)]
        )
        requests_without_proxy = list(
            (request["requestWillBeSent"]) for request in stats[int(len(stats) / 2) :]
        )
        average_request_with_proxy = sum(requests_with_proxy) / len(requests_with_proxy)
        average_request_without_proxy = sum(requests_without_proxy) / len(
            requests_without_proxy
        )

        responses_with_proxy = list(
            (response["responseReceived"]) for response in stats[: int(len(stats) / 2)]
        )
        responses_without_proxy = list(
            (response["responseReceived"]) for response in stats[int(len(stats) / 2) :]
        )
        average_response_with_proxy = sum(responses_with_proxy) / len(
            responses_with_proxy
        )
        average_response_without_proxy = sum(responses_without_proxy) / len(
            responses_without_proxy
        )

        requests_percent = (
            100 * average_request_without_proxy / average_request_with_proxy
        )
        response_percent = (
            100 * average_response_without_proxy / average_response_with_proxy
        )
        if int(round(requests_percent)) > 95 and int(round(response_percent)) > 95:
            return True
        return False


class CurlResponseAnalyzer:
    """Analyse curl response."""

    def __init__(self, response: str):
        self._response = response

    def get_status_code(self) -> int:
        pattern = r"HTTP/(\d|(\d\.\d))\s(\d+)"
        result = re.compile(pattern).search(self._response)
        if result is not None:
            return int(result[3])
