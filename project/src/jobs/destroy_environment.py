import os
import logging

from pyats.easypy import run

import src


_scripts_dir = os.path.join(src.__path__[0], "testscripts")


def main(runtime):

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.INFO
    )

    testscript = os.path.join(_scripts_dir, "environment_cleanup.py")
    run(runtime=runtime, testscript=testscript)
