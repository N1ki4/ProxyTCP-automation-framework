import os
import logging

from pyats.easypy import run

import src

_scripts_dir = os.path.join(src.__path__[0], "envscripts")


def main(runtime):

    logging.getLogger().setLevel(logging.INFO)

    testscript = os.path.join(_scripts_dir, "systemundertest_setup.py")
    run(runtime=runtime, testscript=testscript)
