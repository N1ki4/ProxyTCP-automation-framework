# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
from typing import Tuple, Sequence


def log_table_resources(
    hosts: Sequence[str],
    runs: int,
    proxyied_stats: Sequence[Tuple[int, int]],
    direct_stats: Sequence[Tuple[int, int]],
    request_avg_success: Sequence[float],
    response_avg_success: Sequence[float],
) -> str:

    preface = f"RUNS: {runs}\n" f"HOSTS:\n"
    for i in hosts:
        preface += f"{4*' '}{i}\n"

    table_name = "\nTABLE - resources\n"
    table_head = (
        f"{''.center(94, '_')}\n"
        f"|{'host'.center(20)}|{'proxy ON'.center(23)}|{'proxy OFF'.center(23)}|"
        f"{'Success rate'.center(23)}|\n"
        f"|{''.center(20)}|{''.center(71, '_')}|\n"
        f"|{''.center(20)}|{'requests'.center(11)}|{'responses'.center(11)}|"
        f"{'requests'.center(11)}|{'responses'.center(11)}|"
        f"{'requests'.center(11)}|{'responses'.center(11)}|\n"
        f"|{''.center(92, '_')}|\n"
    )
    table_content = ""
    for i, stat in enumerate(
        zip(proxyied_stats, direct_stats, request_avg_success, response_avg_success)
    ):
        host = hosts[i]
        host = (host[:18] + "..") if len(host) > 20 else host
        table_content += (
            f"|{host.ljust(20)}|"
            f"{str(stat[0][0])[:4].ljust(11)}|{str(stat[0][1])[:4].ljust(11)}|"
            f"{str(stat[1][0])[:4].ljust(11)}|{str(stat[1][1])[:4].ljust(11)}|"
            f"{str(stat[2])[:4].ljust(11)}|{str(stat[3])[:4].ljust(11)}|\n"
            f"|{''.center(92, '_')}|\n"
        )
    return preface + table_name + table_head + table_content


def log_table_time(
    host: str,
    runs: int,
    proxyied_times: Sequence[float],
    direct_times: Sequence[float],
    avg_success: Sequence[float],
) -> str:

    preface = f"RUNS: {runs}\n" f"HOST: {host}\n"

    table_name = "\nTABLE - loading time, ms\n"
    table_head = (
        f"{''.center(50, '_')}\n"
        f"|{'run'.center(10)}|{'proxy ON'.center(11)}|{'proxy OFF'.center(11)}|"
        f"{'delay rate'.center(13)}|\n"
        f"|{''.center(48, '_')}|\n"
    )
    table_content = ""
    for i, stat in enumerate(zip(proxyied_times, direct_times, avg_success)):
        table_content += (
            f"|{str(i).ljust(10)}|"
            f"{str(stat[0]).ljust(11)}|{str(stat[1]).ljust(11)}|{str(stat[2])[:4].ljust(13)}|\n"
            f"|{''.center(48, '_')}|\n"
        )
    return preface + table_name + table_head + table_content


# if __name__ == "__main__":
# p = ((45, 43), (30, 29))
# d = ((50, 50), (32, 32), (16, 16), (0,0))
# r = 5
# h = ["host1444444444444444444.com", "host2.com", "host3.com"]
# rqa = (0.95, 0.98, 1.0)
# rsp = (0.96, 0.97, 1.0)

# t = log_table_resources(
#     hosts=h, runs=r, direct_stats=d, proxyied_stats=p,
#     request_avg_success=rqa, response_avg_success=rsp
# )
# p = (6, 6, 7.1, 8, 9, 7)
# d = (5, 5, 4, 5.6, 4, 5)
# s = (0.8, 0.9, 0.7, 0.8, 0.9, 0.8)
# r = 6
# h = "host2.com"
# t = log_table_time(
#     host=h, runs=r, direct_times=d, proxyied_times=p, avg_success=s
# )
