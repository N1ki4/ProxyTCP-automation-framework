import os
import logging

from pyats.easypy import run

import src


_scripts_dir = os.path.join(src.__path__[0], "testscripts")
_datafile_dir = os.path.join(src.__path__[0], "datafiles")


def main(runtime):

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("unicon").setLevel(logging.INFO)

    testscript = os.path.join(_scripts_dir, "regression.py")
    datafile = os.path.join(_datafile_dir, "regression.yaml")

    run(runtime=runtime, testscript=testscript, datafile=datafile)
