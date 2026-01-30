# Private Cloud Infrastructure & DevOps Platform

![Status](https://img.shields.io/badge/Status-Active-success)
![Infrastructure](https://img.shields.io/badge/Infrastructure-Proxmox-orange)
![IaC](https://img.shields.io/badge/IaC-Pulumi%20%7C%20Terraform-blueviolet)
![Config Mgmt](https://img.shields.io/badge/Config_Mgmt-Ansible-red)

## 📖 Overview

This repository hosts the source code for a fully automated **Private Cloud Infrastructure**, designed to simulate enterprise-grade environments. The project focuses on **Infrastructure as Code (IaC)**, **Configuration Management**, and **Security Automation**.

The goal is to eliminate manual operations ("ClickOps") by defining the entire datacenter state—from Virtual Machine provisioning to application deployment—as code.

### 🏗 Architecture Highlights

* **Hypervisor:** Proxmox VE (Clustered Environment).
* **Provisioning (IaC):** Polyglot approach using **Pulumi (Python)** for programmatic logic and **Terraform** for declarative state management.
* **Configuration Management:** **Ansible** playbooks for OS hardening, security compliance, and software installation.
* **Network Security:** Strict segmentation (DMZ vs LAN), **mTLS** authentication for internal services, and software-defined firewalls (UFW/pfSense).
* **Application Layer:** Docker-based container orchestration with Traefik as the Ingress Controller/Load Balancer.

---

## 🛠 Technology Stack

| Domain | Tools & Technologies |
| :--- | :--- |
| **Infrastructure Provisioning** | **Pulumi** (Python SDK), **Terraform** (HCL), Proxmox API |
| **Configuration Management** | **Ansible**, Jinja2 Templating, Bash Scripting |
| **Containerization** | Docker, Docker Compose |
| **Networking & Security** | Traefik (Reverse Proxy), OpenSSL (Internal PKI), WireGuard (VPN), UFW |
| **Backend Development** | Python (Django/Flask for custom internal tools), PostgreSQL, Redis |
| **CI/CD** | Git, GitHub Actions (planned) |

---

## 📂 Repository Structure

```text
.
├── Ansible/                 # Configuration Management Layer
│   ├── inventory/           # Dynamic & Static Inventories (Prod/Dev)
│   ├── playbooks/           # Orchestration logic (site.yml)
│   ├── roles/               # Modular roles (Security, Docker, GitLab, etc.)
│   └── certs/               # Internal PKI & mTLS definitions
│
├── Pulumi/                  # Infrastructure as Code (Python)
│   ├── infrastructure/      # VM & LXC Provisioning logic (Proxmox Provider)
│   └── apps/                # Application stack definitions (Custom VPN, DBs)
│
├── Terraform/               # Infrastructure as Code (HCL) - *Alternative Provisioner*
│   ├── modules/             # Reusable infrastructure modules
│   └── main.tf              # State definition for core resources
│
└── orchestrate.py           # Python glue-code for triggering deployment workflows
```

## How to use it

Inside the Pulumi directory, first add the configs that you need and run `pulumi up`. After that, go into the infrastructure directory and run `pulumi up` and wait for the machines to spin up and get configured with Ansible. After that, go into the apps directory and run `pulumi up` to spin up the docker containers for the apps. 
