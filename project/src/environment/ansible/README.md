# Ansible environment autodeploy

This package have 3 playbooks:
- Docker and docker-compose (installed on two client endpoints)
- Tshark (installed on three enpoints, neccessary for packet capturing testing)
- Proxy (program under the test itself)

Running from the main entrypoint
```bash
ansible-playbooks main.yml
```
# Directories structure
- **group_vars/all** (contains username to create on virtual machines and path to the ssh identity file)
- **playbooks/** (main directory with ansible playbooks)
- **playbooks/files** (files to copy on virtual machines)
- **ansible.cfg** (file with configurations like: path to inventory, ssh key checking)
- **main.yml** (entrypoint to gather all playbooks)