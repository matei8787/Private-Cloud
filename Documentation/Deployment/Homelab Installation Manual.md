## 1. Prerequisites (The Control Node)

Before running any automation, the "admin" computer (your laptop or a jump box) needs specific tools.

#### **Dependencies:** All the python dependencies are in the requirements.txt
#### Environment variables:
- **Infrastructure Access (Proxmox)**
	- `proxmoxUrl`: The full URL to the Proxmox API (e.g., `https://10.42.0.1:8006/api2/json`)
	- `proxmoxNodeName`: The target node name in the cluster (e.g., `pve`).
	- `proxmoxUser`: The username for authentication (e.g., `root@pam`).
	- `proxmoxPass` **[Secret]**: The password for the Proxmox user.
	- `proxmoxTokenId`: The API Token ID for automation.
	- `proxmoxTokenSecret` **[Secret]**: The API Token Secret.
- **Network Topology**
	- `lanBridgeName`: The Proxmox bridge for the internal LAN (e.g., `vmbr1`).
	- `dmzBridgeName`: The Proxmox bridge for the DMZ (e.g., `vmbr2`).
	- `dmzIpAddress`: Static IP for the DMZ interface.
	- `pfsHost`: IP address of the pfSense firewall.
- **Virtual Machine Templates**
	- `ubuntuFileId`: The storage ID of the Ubuntu ISO (e.g., `local:iso/ubuntu-22.04.iso`).
	- `ubuntuTemplateId`: The ID of the VM template to clone (e.g., `9000`).
	- `sshPublicKey`: The public SSH key to inject into all created VMs.
- **Application Secrets & Database**
	- `appSqlName`: Name of the database to create.
	- `appSqlEngine`: Database engine type (e.g., `django.db.backends.postgresql`).
	- `postgresPass` **[Secret]**: The master password for the Postgres user.
	- `appSecret` **[Secret]**: The Django `SECRET_KEY`.
	- `dockerSecret` **[Secret]**: Password/Token for the Docker registry/user.
	- `gitlabRunnerKey` / `gitlabServerKey`: Registration tokens for CI/CD.
- **PKI & Certificates (Ansible/Internal SSL)**
	- `pfsTestCA` **[Secret]**: The refId of the Testing CA from pfSense.
	- `pfsKey` **[Secret]**: The private key for the VPN service.
	- **INTERNAL CERT FOR NGINX**: Cert for Nginx-Traefik SSL Communication
	- **INTERNAL CHAIN FOR NGINX**: Chain for Nginx-Traefik SSL Communication
- **Connectivity:**
    - "Ensure the Control Node is on the same subnet as the Proxmox Management Interface, or at least that it can access it (Works with VPN)"
- **Already Configured Infrastructure**
	- You should have the CAs already made in pfSense.
	- The certs to give to Nginx and Traefik.
	-  The networks for the Servers and DMZ subnets should alredy be created.
	- The firewall rules set up for access.

### Infrastructure Provisioning and Application Deployment

**Goal:** Transform the only pfSense Proxmox environment into a segmented virtual network with Two running VMs.
#### The Architecture (How it works)

> "This project utilizes a **Custom Builder Pattern** wrapped in a multi-stack Pulumi architecture. A dedicated Python module abstracts the complexities of the Proxmox and Docker APIs.
> 
> To ensure separation of concerns, the deployment is split into three interdependent stacks:
> 
> 1. **Config Stack:** Centralizes secret management and environment variables, exporting them as a `StackReference`.
>     
> 2. **Infrastructure Stack:** Consumes the config to provision VMs and automatically triggers Ansible for OS hardening.
>     
> 3. **Apps Stack:** Consumes the infrastructure outputs to deploy Docker containers via the Docker provider.
>     
> 
> The `ProxmoxServerBuilder` class enforces security defaults (disabling cloud-init generic users, pre-loading SSH keys) automatically for every instance, ensuring that no VM can be deployed in an insecure state."
#### Execution Steps
###### **Step 1: Initialize Project Stacks** Select the development environment for all three layers of the pipeline.
``` bash
	cd Pulumi/config && pulumi stack select dev
	cd ../infrastructure && pulumi stack select dev
	cd ../apps && pulumi stack select dev
	cd ../../
```
###### **Step 2: Hydrate Configuration (The Config Stack)** Populate the environment variables and secrets. This step creates the "Contract" that the other stacks will read from
``` bash
	cd Pulumi/configs
	pulumi config set ENV_VAR_NAME ENV_VAR_VALUE
	...
	pulumi up --yes
	cd ../../
```
- **Expectation:** The CLI will verify that all variables are set and export them as Stack Outputs.
###### **Step 3: Provision Infrastructure & Harden OS (The Infra Stack)** Deploys the Virtual Machines and Bridges to Proxmox. Once the VMs are online, this step automatically triggers the Ansible playbooks to apply security configurations.
``` bash
	cd Pulumi/infrastructure
	pulumi up --yes
	cd ../../
```
- **Expectation:** You will see the creation of the `Services` and `DMZ` VMs.
- **Internal Action:** Watch the logs for "Ansible Playbook finished successfully" indicating the OS has been hardened.
###### **Step 4: Deploy Applications (The Apps Stack)** Connects to the now-secure VMs and spins up the Docker containers.
``` bash
	cd Pulumi/apps
	pulumi up --yes
	cd ../../
```
- **Expectation:** The Traefik Reverse Proxy will start on the DMZ node, and the VPN Provisioner (plus DB/Redis) will start on the Services node.
### Verification
###### Try to ssh into one of the created VMs, it will work.
###### Navigate to https://10.x.x.x:yyyy, it  will work
### Infrastructure Teardown (Cleanup)

**Goal:** Cleanly remove all provisioned resources (VMs, Bridges, Containers) in the correct dependency order.
#### Execution Steps
###### Step 1: Destroy Apps
``` bash
	cd Pulumi/apps
	pulumi destroy --yes
	cd ../../
```
- **Reason:** Must stop containers before deleting the VMs they run on.
###### Step 2: Destroy Infrastructure
``` bash
	cd Pulumi/infrastructure 
	pulumi destroy --yes
	cd ../../
```
- **Reason:** Removes VMs from Proxmox.

### Troubleshooting
| Symptom                 | Probable Cause                                    | Resolution                                                                                                |
| ----------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Ansible Unreachable     | SSH-key not added on the user running the command | ssh-add the private key paired with the public key deployed.                                              |
| Traefik: 404 Not Found  | Usually an internal problem with the apps.        | Wait 10-20 second. If it didn't work, ssh into the Services server and docker logs                        |
| Pulumi: Stack is locked | A previous run was interrupted (CTRL+C)           | pulumi stack export > tmp.json, remove all resources from tmp.json and <br>pulumi stack import < tmp.json |

### Diagram
![Deployment Diagram](./Diagrama.jpg)