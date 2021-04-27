import os

from pyats import aetest

import src
from src.environment.google_cloud_setup import builder


parameters = {"root": src.__path__[0]}


class GoogleCloudCleanUp(aetest.Testcase):
    """Deleting Google Cloud setup."""

    @aetest.test
    def main(self, root, service_key):
        _build_file = os.path.join(
            root, "environment", "google_cloud_setup", "setup.config.yaml"
        )
        setup = builder.Builder(build_file=_build_file, service_acc_key=service_key)
        setup.execute_teardown_scenario()


if __name__ == "__main__":
    import sys
    import argparse
    import logging

    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.DEBUG
    )

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--service-key", dest="service_key")

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(service_key=args.service_key)
