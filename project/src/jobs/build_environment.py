import os
import sys
import argparse
import logging

from pyats.easypy import run

import src

_scripts_dir = os.path.join(src.__path__[0], "envscripts")


def main(runtime):
    max_reps = 2

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.INFO
    )
    _log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--service-key", dest="service_key")
    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])

    tasks = ("environment_setup.py", "systemundertest_setup.py")

    for script in tasks:
        task_success = True
        testscript = os.path.join(_scripts_dir, script)
        for i in range(max_reps):
            result = run(
                runtime=runtime, testscript=testscript, service_key=args.service_key
            )
            if result:
                break
            if i != max_reps - 1:
                _log.info("Job failed, repeating attempt!")
            else:
                task_success = False
                _log.error("Job failed!")
        if not task_success:
            break
