terraform {
  required_providers {
    proxmox = {
        source = "bpg/proxmox"
    }
  }
}

provider "proxmox" {
    endpoint = var.pxm_url
    api_token = "${var.pxm_token_id}=${var.pxm_token_secret}"
    insecure = true
    ssh {
        agent = true
    }
}

module "services_server" {
    source = "./modules/proxmox_vm"
    vm_name = "Service"
    memory = "4096"
    ssh = {
      public_key = var.ssh_public_key
    }
    network_config = {
      bridge = "service"
      vlan = 10
      ip = "10.69.10.5/24"
      gateway = "10.69.10.1"
      firewall = false
    }

    storage = [{
        size = 32
    }]
    cpu = {
      cores = 3
    }
    init_datastore = "local-zfs"
}