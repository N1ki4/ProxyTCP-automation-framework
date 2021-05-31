from abc import ABC, abstractmethod
import json
import re

import polling
from google.auth.transport import requests
from google.oauth2 import service_account
from requests.exceptions import HTTPError


def retry_on_error(max_attempts):
    """Retry decorator for 400 error."""

    def inner(func):
        def wrapper(self):
            for i in range(max_attempts):
                response = func(self)
                if self._exceptions and i < max_attempts - 1:
                    self._exceptions = []
                else:
                    return response

        return wrapper

    return inner


class Controller(ABC):
    """Base controller class constructor."""

    def __init__(self, project):
        self._project = project
        self._session = None
        self._created_status = False
        self._deleted_status = False
        self._data = None
        self._exceptions = []

        service_key = project.credentials["service-acc-key"]
        scopes = project.credentials["access-scopes"]
        credentials = service_account.Credentials.from_service_account_file(
            service_key, scopes=scopes
        )
        self._session = requests.AuthorizedSession(credentials=credentials)

    def _is_good_response(self, response):
        """Check that response status code is in range 200-299 or eq to 409."""
        result = True
        try:
            response.raise_for_status()
        except HTTPError as exception:
            if response.status_code != 409:
                result = False
                self._exceptions.append(exception)
        return result

    def _wait_for_deletion_complete(self):
        """Poll GET request till 404 occured."""
        try:
            polling.poll(lambda: self.get().status_code == 404, timeout=120, step=2)
        except polling.TimeoutException as exception:
            self._exceptions.append(exception)
        else:
            self._deleted_status = True

    def _wait_for_creation_complete(self):
        """Poll crreation status, individual for each case."""

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class NetworkController(Controller):
    """Compute engine's Network API Controller."""

    @property
    def created_status(self):
        return self._created_status

    @property
    def deleted_status(self):
        return self._deleted_status

    @property
    def data(self):
        return self._data

    @property
    def exceptions(self):
        return self._exceptions

    def _wait_for_creation_complete(self):
        # wait untill all subnets are created
        def subnets_created():
            response_data = json.loads(self.get().content)
            subnets = response_data.get("subnetworks", [])
            if len(subnets) < 25:
                return False
            return True

        try:
            polling.poll(lambda: subnets_created() is True, timeout=60, step=2)
        except polling.TimeoutException as exception:
            self._exceptions.append(exception)
        else:
            self._created_status = True

    def _get_data(self):
        response_data = json.loads(self.get().content)
        self._data = {"network": response_data["name"]}

    def create(self):
        """Build and send API 'insert' request."""
        method = "POST"
        url = f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/global/networks"
        body = {
            "autoCreateSubnetworks": True,
            "description": "",
            "mtu": 1460.0,
            "name": self._project.network,
            "routingConfig": {"routingMode": "REGIONAL"},
            "selfLink": f"projects/{self._project.id}/global/networks/{self._project.network}",
        }
        response = self._session.request(method=method, url=url, data=json.dumps(body))

        if self._is_good_response(response):
            self._wait_for_creation_complete()
            self._get_data()

        return response

    def get(self):
        """Build and send API 'get' request."""
        method = "GET"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}"
            f"/global/networks/{self._project.network}"
        )

        response = self._session.request(method=method, url=url)
        return response

    def delete(self):
        """Build and send API 'delete' request."""

        method = "DELETE"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/global"
            f"/networks/{self._project.network}"
        )

        response = self._session.request(method=method, url=url)
        self._wait_for_deletion_complete()
        return response


class InstanceController(Controller):
    """Controller for InstancesClient class of google-cloud-compute lib."""

    def __init__(self, project, instance, template=None):
        super().__init__(project)
        self._template = template
        self._instance = instance

    @property
    def created_status(self):
        return self._created_status

    @property
    def deleted_status(self):
        return self._deleted_status

    @property
    def data(self):
        return self._data

    @property
    def exceptions(self):
        return self._exceptions

    def _wait_for_creation_complete(self):
        # wait untill VM's network interfaces are configured, that's a bit of latency
        def ip_identified():
            response_data = json.loads(self.get().content)
            net_ip = response_data["networkInterfaces"][0].get("networkIP")
            nat_ip = response_data["networkInterfaces"][0]["accessConfigs"][0].get(
                "natIP"
            )
            if not net_ip or not nat_ip:
                return False
            return True

        try:
            polling.poll(lambda: ip_identified() is True, timeout=60, step=2)
        except polling.TimeoutException as exception:
            self._exceptions.append(exception)
        else:
            self._created_status = True

    def _get_data(self):
        response_data = json.loads(self.get().content)
        self._data = {
            "name": response_data["name"],
            "network_ip": response_data["networkInterfaces"][0].get("networkIP"),
            "nat_ip": response_data["networkInterfaces"][0]["accessConfigs"][0].get(
                "natIP"
            ),
        }

    def _identify_subnet(self):
        zone = self._instance.zone
        return re.compile(r"\w+-\w+").search(zone)[0]

    @retry_on_error(max_attempts=15)
    def create(self):
        """Build and send API 'insert' request."""
        method = "POST"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/zones"
            f"/{self._instance.zone}/instances"
        )
        body = {
            "name": self._instance.name,
            "zone": f"projects/{self._project.id}/zones/{self._instance.zone}",
            "machineType": f"projects/{self._project.id}/zones/{self._instance.zone}"
            f"/machineTypes/{self._template.machine_type}",
            "tags": {"items": self._instance.tags},
            "disks": [
                {
                    "type": "PERSISTENT",
                    "boot": True,
                    "mode": "READ_WRITE",
                    "autoDelete": True,
                    "deviceName": self._instance.name,
                    "initializeParams": {
                        "sourceImage": f"projects/ubuntu-os-cloud/global/images/family"
                        f"/{self._template.os}",
                        "diskType": f"projects/{self._project.id}/zones/{self._instance.zone}"
                        f"/diskTypes/pd-balanced",
                        "diskSizeGb": str(self._template.disk_size),
                    },
                    "diskEncryptionKey": {},
                }
            ],
            "canIpForward": True,
            "networkInterfaces": [
                {
                    "subnetwork": f"projects/{self._project.id}/regions"
                    f"/{self._identify_subnet()}/subnetworks"
                    f"/{self._project.network}",
                    "accessConfigs": [
                        {
                            "name": "External NAT",
                            "type": "ONE_TO_ONE_NAT",
                            "networkTier": "PREMIUM",
                        }
                    ],
                }
            ],
            "description": "",
            "serviceAccounts": [
                {
                    "email": self._session.credentials.service_account_email,
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/trace.append",
                    ],
                }
            ],
        }

        response = self._session.request(method=method, url=url, data=json.dumps(body))
        if self._is_good_response(response):
            self._wait_for_creation_complete()
            self._get_data()

        return response

    def get(self):
        """Build and send API 'get' request."""
        method = "GET"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/zones"
            f"/{self._instance.zone}/instances/{self._instance.name}"
        )

        response = self._session.request(method=method, url=url)
        return response

    @retry_on_error(max_attempts=2)
    def delete(self):
        """Build and send API 'delete' request."""

        method = "DELETE"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/zones"
            f"/{self._instance.zone}/instances/{self._instance.name}"
        )

        response = self._session.request(method=method, url=url)
        self._wait_for_deletion_complete()
        return response


class FirewallController(Controller):
    """Controller for FirewallsClient class of google-cloud-compute lib."""

    def __init__(self, project, firewall_rule):
        super().__init__(project)
        self._firewall_rule = firewall_rule

    @property
    def created_status(self):
        return self._created_status

    @property
    def deleted_status(self):
        return self._deleted_status

    @property
    def data(self):
        return self._data

    @property
    def exceptions(self):
        return self._exceptions

    def _get_data(self):
        response_data = json.loads(self.get().content)
        self._data = {
            "name": response_data["name"],
            "allowed": response_data["allowed"][0],
            "tags": response_data["targetTags"],
        }

    def create(self):
        """Build and send API 'insert' request."""
        method = "POST"
        url = f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/global/firewalls"
        body = {
            "name": self._firewall_rule.name,
            "network": f"projects/{self._project.id}/global/networks/{self._project.network}",
            "direction": "INGRESS",
            "priority": self._firewall_rule.priority,
            "targetTags": self._firewall_rule.tags,
            "allowed": [
                {
                    "IPProtocol": self._firewall_rule.protocol,
                    "ports": self._firewall_rule.ports,
                }
            ],
            "sourceRanges": self._firewall_rule.source_ip_ranges,
        }
        response = self._session.request(method=method, url=url, data=json.dumps(body))
        self._created_status = True
        self._get_data()
        return response

    def get(self):
        """Build and send API 'get' request."""
        method = "GET"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/global"
            f"/firewalls/{self._firewall_rule.name}"
        )

        response = self._session.request(method=method, url=url)
        return response

    def delete(self):
        """Build and send API 'delete' request."""

        method = "DELETE"
        url = (
            f"https://www.googleapis.com/compute/v1/projects/{self._project.id}/global"
            f"/firewalls/{self._firewall_rule.name}"
        )

        response = self._session.request(method=method, url=url)
        self._wait_for_deletion_complete()
        return response
