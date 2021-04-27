import os
import logging
import yaml

from src.environment.google_cloud_setup import components, controllers, sshmanager

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)


class Builder:

    _keys = ("project", "instance-templates", "instances", "firewall-rules")

    def __init__(self, build_file: str):
        """Load and parse setup.config.yaml file into python objects."""

        self._build = None
        self._project = None
        self._templates = None
        self._user = None
        self._instances = None
        self._firewall = None
        self._response_data = dict()
        self._key = None

        def load_yaml(file: str) -> dict:
            with open(file) as x:
                return yaml.load(x, Loader=yaml.FullLoader)

        build = load_yaml(build_file)
        self._build = build

        self._user = build["instance-user"]["name"]

        self._project = components.Project(
            id=build["project"]["id"],
            network=build["project"]["network"],
            credentials=build["project"]["credentials"],
        )
        self._templates = [
            components.InstTemplate(
                name=entry["name"],
                machine_type=entry["machine-type"],
                disk_size=entry["disk-size"],
                os=entry["os"],
            )
            for entry in build["instance-templates"]
        ]
        self._instances = [
            components.Instance(
                name=entry["name"],
                zone=entry["zone"],
                external_ip=entry["external-ip"],
                tags=entry["tags"],
                from_=entry["from"],
            )
            for entry in build["instances"]
        ]
        self._firewall = [
            components.FirewallRule(
                name=entry["name"],
                source_ip_ranges=entry["source-ip-ranges"],
                priority=entry["priority"],
                ports=entry["ports"],
                protocol=entry["protocol"],
                tags=entry["tags"],
            )
            for entry in build["firewall-rules"]
        ]

    def _create_network(self):
        # instantiate NetworkController object to get access to API
        # create network
        # check network creation, also retrieve network name
        network = controllers.NetworkController(self._project)
        network.create()
        if network.created_status is True:
            _log.info(f'Created network `{network.data["network"]}`')
            self._response_data.update({"network": network.data})
        else:
            error = network.exceptions[0]
            _log.error(f"Error occured while creating network: {error}")
            raise error

    def _delete_network(self):
        # instantiate NetworkController object to get access to API
        # delete network
        # check network deletion
        network = controllers.NetworkController(self._project)
        network.delete()
        if network.deleted_status is True:
            _log.info(f"Deleted network `{self._project.network}`")
        else:
            error = network.exceptions[0]
            _log.error(f"Error occured while deleting network: {error}")
            raise error

    def _create_instances(self):
        # loop through the list of instances
        # get instance template
        # instantiate InstanceController object for each instance to get access to API
        # create instance
        # check instance creation
        # retrieve following data: name, network_ip, nat_i_
        for inst in self._instances:
            inst_template_name = inst.from_
            inst_template = None
            for templ in self._templates:
                if templ.name == inst_template_name:
                    inst_template = templ
                    break

            instance = controllers.InstanceController(
                project=self._project, template=inst_template, instance=inst
            )
            instance.create()
            if instance.created_status is True:
                _log.info(
                    f'Created instance `{instance.data["name"]}`, network IP:'
                    f'{instance.data["network_ip"]}, NAT IP: {instance.data["nat_ip"]}'
                )
                key = instance.data["name"]
                self._response_data.update({key: instance.data})
            else:
                error = instance.exceptions[0]
                _log.error(f"Error occured while creating instance: {error}")
                raise error

    def _delete_instances(self):
        # loop through the list of instances
        # instantiate InstanceController object for each instance to get access to API
        # delete instance
        for inst in self._instances:
            instance = controllers.InstanceController(
                project=self._project, instance=inst
            )
            instance.delete()
            if instance.deleted_status is True:
                _log.info(f"Deleted instance `{inst.name}`")
            else:
                error = instance.exceptions[0]
                _log.error(f"Error occured while deleting instance: {error}")
                raise error

    def _apply_firewall_rules(self):
        # loop through the list of rules
        # instantiate FirewallController object for each rule to get access to API
        # create rule
        # check rule creation
        # retrieve following data: name, tags
        for rule in self._firewall:
            firewall_rule = controllers.FirewallController(
                project=self._project, firewall_rule=rule
            )
            firewall_rule.create()
            if firewall_rule.created_status is True:
                _log.info(
                    f'Created firewall rule `{firewall_rule.data["name"]}`: ingress,'
                    f'protocol: {firewall_rule.data["allowed"]["IPProtocol"]},'
                    f'ports: {firewall_rule.data["allowed"]["ports"]}'
                )
                key = firewall_rule.data["name"]
                self._response_data.update({key: firewall_rule.data})
            else:
                error = firewall_rule.exceptions[0]
                _log.error(f"Error occured while creating firewall rule: {error}")
                raise error

    def execute_setup_scenario(self):
        _log.info("Creating test setup ...")

        self._create_network()
        self._create_instances()
        self._apply_firewall_rules()

        _log.info("Test setup successfully created")

    def execute_teardown_scenario(self):
        _log.info("Deleting test setup ...")

        self._delete_instances()
        self._delete_network()

        _log.info("Test setup successfully deleted")

    def add_ssh_keys(self, private_key_file=None):
        if private_key_file is None:
            private_key_file = os.path.join(os.getcwd(), "cloud_access.key")
        manager = sshmanager.SshManager(self._project, self._user)
        manager.create_keys(private_key_file)
        # manager.send_pub_key_to_cloud()
        self._key = private_key_file
        _log.info(
            f"Generated RSA key pair for user `{self._user}`, path to private' \
                'key: `{private_key_file}`"
        )

    def generate_testbed(self, testbed_file="testbed.yaml"):
        testbed = {
            "testbed": {
                "name": self._project.id,
                "credentials": {
                    "default": {
                        "name": self._user,
                        "password": "",
                    },
                },
            },
            "devices": dict(),
        }
        for entry in self._instances:
            device_data = self._response_data.get(entry.name)
            testbed["devices"].update(
                {
                    device_data.get("name"): {
                        "os": "linux",
                        "type": "linux-vm",
                        "connections": {
                            "cli": {
                                "command": f'ssh -i {self._key} {self._user}' \
                                           f'@{device_data.get("nat_ip")}'
                            },
                        },
                    },
                }
            )
            with open(testbed_file, "w") as file:
                file.write(
                    yaml.dump(
                        testbed,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    )
                )
        _log.info(f"Created testbed file `{testbed_file}`")

    def generate_ansible_configs(self, general="all", groups="myhosts.ini"):
        # general data file
        content = (
            f"ansible_user: {self._user}\nansible_ssh_private_key_file: {self._key}"
        )
        with open(general, "w") as file:
            file.write(content)
        # groups data file
        content = "[proxy]"
        for entry in self._instances:
            tag = entry.tags[0]
            device_host = self._response_data.get(entry.name).get("nat_ip")
            if tag == "proxy":
                content += f"\n{entry.name} ansible_host={device_host}"
        content += "\n\n[users]"
        for entry in self._instances:
            tag = entry.tags[0]
            device_host = self._response_data.get(entry.name).get("nat_ip")
            if tag == "usr":
                content += f"\n{entry.name} ansible_host={device_host}"
        with open(groups, "w") as file:
            file.write(content)
        _log.info(f"Created ansible config files `{general}`, `{groups}`")


if __name__ == "__main__":
    builder = Builder("setup.config.yaml")
    builder.execute_setup_scenario()
    # builder.add_ssh_keys()
    # builder.generate_ansible_configs()
    # builder.generate_testbed()
    # builder.execute_teardown_scenario()
