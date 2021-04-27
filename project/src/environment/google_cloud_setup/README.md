# Google Cloud Setup

### Quik Start
#### 1. [Select or create a Cloud Platform project.](https://console.cloud.google.com/project)

#### 2. [Enable billing for your project.](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project)

#### 3. [Enable the Compute Engine API.](https://cloud.google.com/compute/)

### setup.config.yaml

File setup.config.yaml contains project data, configuration of the network to build (including VMs and
firewall rules). It is the main entry point for the cloud setup. Modify this file only.

#### Project
```
# setup.congig.yaml

project:
  id: testing-network-308220
  network: vpc-temp
  credentials:
    service-acc-key: service-acc-key.json
    access-scopes: [https://www.googleapis.com/auth/compute]
```

here:
- id - ID of the Cloud Platform project.
- network - name of the network to create.
- service-acc-key - [service account key file](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#:~:text=You%20can%20create%20a%20service%20account%20key%20using,is%20the%20ID%20of%20your%20Google%20Cloud%20project.).
- access-scopes - mandatory [access scopes](https://developers.google.com/identity/protocols/oauth2/scopes) needed for the authentication.

#### Instances

##### Templates
```
# setup.congig.yaml

instance-templates:
  - name: main-template
    machine-type: e2-medium
    disk-size: 10
    os: ubuntu-2004-lts
    ...
```

here:
- name - name of the template.
- machine-type - [type of the machine](https://cloud.google.com/compute/docs/machine-types#:~:text=Machine%20type%20comparison%20%20%20%20Machine%20types,%20%20Yes%20%207%20more%20rows%20) in terms of performance.
- disk-size - storage disk size in GB.
- os - [operating system](https://cloud.google.com/compute/docs/images/os-details).

##### VMs
```
# setup.congig.yaml

instance-user:
  name: test

instances:
  - name: user-1
    zone: europe-north1-a
    external-ip: ephemeral
    tags: [usr]
    from: main-template
    ...
```

here:
- instance-user - default user of the VM.
- zone - [zone](https://cloud.google.com/compute/docs/regions-zones/) on Google Cloud instance located in.
- tags - instance tags, needed to apply firewall rules.
- from - name of the template to create instance from.

#### Firewall Rules
```
# setup.congig.yaml

firewall-rules:
  - name: allow-ssh
    source-ip-ranges: ["0.0.0.0/0"]
    priority: 1000
    tags:
      -  usr
      -  proxy
    protocol: tcp
    ports: ["22"]
    ...
```

here:
- source-ip-ranges - traffic is only allowed from sources within these IP address ranges. Use CIDR notation when entering ranges.
- priority - rules with lower numbers get prioritized first. Range 0 - 65535
- protocol - ip protocol (tcp, udp, etc.).
- ports - list of ports to apply this rule.
  
### Execution

#### Create Google Cloud setup from setup.config.yaml using class builder.Builder
```python
from builder import Builder

setup = Builder('setup.config.yaml')
setup.execute_setup_scenario()

```

#### Delete Google Cloud setup
```python

setup.execute_teardown_scenario()
```

#### Generate testbed.yaml
```python

setup.generate_testbed()
```