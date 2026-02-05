variable "vm_name" {
    description = "Numele masinii virtuale"
    type = string
}

variable "node" {
    description = "Numele nodului unde se afla instanta"
    type = string
    default = "pve"
}

variable "cpu" {
    description = "CPU config for machine"
    type = object({
        cores = number
        sockets = optional(number, 1)
        type = optional(string, "host")
    })
    default = {
        cores = 2
    }
}

variable "memory" {
    description = "How many MB of RAM"
    default = 2048
    type = number
}

variable "template_id" {
    description = "The ID of the template to clone"
    type = number
    default = 9000
}

variable "ssh" {
    description = "The user and ssh key for the VM"
    type = object({
      public_key = string
      username = optional(string, "dorb") 
    })
}

variable "network_config" {
    description = "The network configuration."
    type = object({
      bridge = optional(string, "vmbr0")
      model = optional(string, "virtio")
      vlan = optional(number, 1)
      firewall = optional(bool, true)
      ip = optional(string, "dhcp")
      gateway = optional(string)
    })
    default = {}
}

variable "storage" {
  description = "Lista de discuri atasate"
  type = list(object({
    size         = number
    interface    = optional(string, "scsi0") 
    datastore_id = optional(string, "local-zfs")
    file_format  = optional(string, "raw")
    ssd          = optional(bool, true)
  }))
  
  default = []
}

variable "init_datastore" {
    description = "datastore_id pentru initialization"
    type = string
}