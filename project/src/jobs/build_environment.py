import os
import sys
import argparse
import logging
from time import sleep

from pyats.easypy import run

import src

_scripts_dir = os.path.join(src.__path__[0], "envscripts")


def main(runtime):
    max_reps = 3

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.INFO
    )
    _log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--service-key", dest="service_key")
    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])

    testscript = os.path.join(_scripts_dir, "environment_setup.py")

    for i in range(max_reps):
        result = run(
            runtime=runtime, testscript=testscript, service_key=args.service_key
        )
        if result:
            break
        if i != max_reps - 1:
            _log.info("Job failed, repeating attempt!")
        else:
            _log.error("Job failed!")
