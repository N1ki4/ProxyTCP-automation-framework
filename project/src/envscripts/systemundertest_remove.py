import os

from pyats import aetest
import ansible_runner

import src


parameters = {"root": src.__path__[0]}


class AnsibleCleanup(aetest.Testcase):
    """Run playbooks. Setup docker, tshark and proxy."""

    @aetest.test
    def main(self, root):
        _ansible_root = os.path.join(root, "environment", "ansible")
        ansible_runner.run(
            project_dir=_ansible_root, playbook="./playbooks/proxy_rm.yml"
        )


if __name__ == "__main__":
    aetest.main()
