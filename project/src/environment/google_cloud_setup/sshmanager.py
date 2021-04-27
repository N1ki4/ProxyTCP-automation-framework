import os
import stat
import json

from google.auth.transport import requests
from google.oauth2 import service_account
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend


class SshManager:
    """Manage ssh key pair creation and adding public key to the cloud."""

    def __init__(self, project, user):
        self._project = project
        self._user = user
        self._session = None
        self._private_key = None
        self._public_key = None

        service_key = project.credentials["service-acc-key"]
        scopes = project.credentials["access-scopes"]
        credentials = service_account.Credentials.from_service_account_file(
            service_key, scopes=scopes
        )
        self._session = requests.AuthorizedSession(credentials=credentials)

    def create_keys(self, private_key_file=None, pub_key_file=None):
        key = rsa.generate_private_key(
            backend=crypto_default_backend(), public_exponent=65537, key_size=2048
        )
        self._private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption(),
        ).decode("utf-8")
        if private_key_file:
            if os.path.exists(private_key_file):
                os.chmod(private_key_file, stat.S_IRWXU)
            with open(private_key_file, "w") as file:
                file.write(self._private_key)
                os.chmod(private_key_file, stat.S_IREAD)

        self._public_key = (
            key.public_key()
            .public_bytes(
                crypto_serialization.Encoding.OpenSSH,
                crypto_serialization.PublicFormat.OpenSSH,
            )
            .decode("utf-8")
        )
        if pub_key_file:
            with open(pub_key_file, "w") as file:
                file.write(self._public_key)

    def get_fingerprint(self):
        method = "GET"
        url = f"https://compute.googleapis.com/compute/v1/projects/{self._project.id}"

        response = self._session.request(method=method, url=url)
        response_data = json.loads(response.content)
        return response_data.get("commonInstanceMetadata").get("fingerprint")

    def send_pub_key_to_cloud(self):
        fingerprint = self.get_fingerprint()
        method = "POST"
        url = (
            f"https://compute.googleapis.com/compute/v1/projects/{self._project.id}"
            "/setCommonInstanceMetadata"
        )
        body = {
            "fingerprint": fingerprint,
            "items": [
                {
                    "key": "ssh-keys",
                    "value": f"{self._user}:{self._public_key} {self._user}",
                }
            ],
        }
        response = self._session.request(method=method, url=url, data=json.dumps(body))
        return response
