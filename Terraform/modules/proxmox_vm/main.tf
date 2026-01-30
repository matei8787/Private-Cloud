terraform {
  required_providers {
    proxmox = {
        source = "bpg/proxmox"
    }
  }
}

resource "proxmox_virtual_environment_vm" "this" {
    name = var.vm_name
    node_name = var.node
    cpu {
        cores = var.cpu.cores
        sockets = var.cpu.sockets
        type = var.cpu.type
    }

    memory {
      dedicated = var.memory
    }

    dynamic "disk" {
      for_each = var.storage
      content {
        datastore_id = disk.value.datastore_id
        interface = disk.value.interface
        file_format = disk.value.file_format
        size = disk.value.size
        ssd = disk.value.ssd
      }
    }
    clone {
        vm_id = var.template_id
        full = true
    }

    initialization {
        datastore_id = var.init_datastore
        ip_config {
            ipv4 {
              address = var.network_config.ip
              gateway = var.network_config.gateway
            }
        }
        user_account {
          username = var.ssh.username
          keys = [ var.ssh.public_key ]
        }
    }

    network_device {
      bridge = var.network_config.bridge
      model = var.network_config.model
      vlan_id = var.network_config.vlan
      firewall = var.network_config.firewall
    }

}