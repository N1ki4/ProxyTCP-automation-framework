import os
import logging

from pyats import aetest, topology
import ansible_runner

import src
from src.classes.remote_tools import SeleniumGrid
from src.environment.google_cloud_setup import builder


_log = logging.getLogger(__name__)


parameters = {"root": src.__path__[0]}


class GoogleCloudSetup(aetest.Testcase):
    """Creating Google Cloud setup."""

    @aetest.test
    def main(self, steps, root, service_key):
        print(service_key)
        _build_file = os.path.join(
            root, "environment", "google_cloud_setup", "setup.config.yaml"
        )
        _testbed = os.path.join(root, "testbed.yaml")
        _ansible_general = os.path.join(
            root, "environment", "ansible", "group_vars", "all"
        )
        _ansible_hosts = os.path.join(root, "environment", "ansible", "myhosts.ini")
        _ssh_file = os.path.join(
            root, "environment", "google_cloud_setup", "cloud_access.key"
        )
        try:
            setup = builder.Builder(build_file=_build_file, service_acc_key=service_key)
            with steps.start("Executing main building scenario"):
                setup.execute_setup_scenario()
            with steps.start("Generating SSH keys"):
                setup.add_ssh_keys(private_key_file=_ssh_file)
            with steps.start("Generating ansible config files"):
                setup.generate_ansible_configs(
                    general=_ansible_general, groups=_ansible_hosts
                )
            with steps.start("Generating testbed"):
                setup.generate_testbed(testbed_file=_testbed)
        except Exception as exp:
            self.errored(f"{exp} occured!", goto=["exit"])


class AnsibleSetup(aetest.Testcase):
    """Run playbooks. Setup docker, tshark and proxy."""

    @aetest.test
    def main(self, root):
        _ansible_root = os.path.join(root, "environment", "ansible")

        try:
            ansible_runner.run(project_dir=_ansible_root, playbook="main.yml")
        except Exception as exp:
            self.errored(f"{exp} occured!", goto=["exit"])


class DeployGrid(aetest.Testcase):
    """Deploy Selenium Grid."""

    @aetest.setup
    def setup(self, root):
        testbed_file = os.path.join(root, "testbed.yaml")
        testbed = topology.loader.load(testbed_file)
        grid_servers = [v for k, v in testbed.devices.items() if "proxy" not in k]
        self.parent.parameters.update(
            [
                ("grid_servers", grid_servers),
            ]
        )

    @aetest.test
    def main(self, grid_servers):
        for server in grid_servers:
            grid = SeleniumGrid(server)
            grid.up()


class CommonCleanup(aetest.CommonCleanup):
    pass


if __name__ == "__main__":
    import sys
    import argparse

    _log.setLevel(logging.DEBUG)
    logging.getLogger("src.environment.google_cloud_setup.builder").setLevel(
        logging.DEBUG
    )

    parser = argparse.ArgumentParser(description="standalone parser")
    parser.add_argument("--service-key", dest="service_key")

    args, sys.argv[1:] = parser.parse_known_args(sys.argv[1:])
    aetest.main(service_key=args.service_key)
