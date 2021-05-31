import os
import sys
import argparse
import logging

from pyats.easypy import run

import src


_scripts_dir = os.path.join(src.__path__[0], "envscripts")


def main(runtime):

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.INFO
    )

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--service-key", dest="service_key")
    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])

    testscript = os.path.join(_scripts_dir, "environment_cleanup.py")
    run(runtime=runtime, testscript=testscript, service_key=args.service_key)
