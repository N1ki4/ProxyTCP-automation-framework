import os
import logging

from pyats.easypy import run

import src


_scripts_dir = os.path.join(src.__path__[0], "testscripts")
_datafile_dir = os.path.join(src.__path__[0], "datafiles")


def main(runtime):

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("unicon").setLevel(logging.ERROR)

    tasks = (
        ("socks.py", "socks.yaml"),
        ("tls.py", "tls.yaml"),
        ("browser.py", "browser.yaml"),
    )

    for script, data in tasks:

        testscript = os.path.join(_scripts_dir, script)
        datafile = os.path.join(_datafile_dir, data)

        run(runtime=runtime, testscript=testscript, datafile=datafile)
