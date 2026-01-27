"""A Python Pulumi program"""

import pulumi
import imports
from Proxmox.server import ProxmoxServerBuilder
from Proxmox.provider import ProxmoxProviderBuilder
import pulumi_command as command
import yaml
import os

def create_vms(provider=None):
      serverVM = (ProxmoxServerBuilder(imports.node_name, imports.template_id, provider)
            .set_name("server-vm")
            .set_server_name(imports.server_name)
            .set_resources(cpu=imports.server_cpus, memory=imports.server_memory, storage=imports.server_storage, network_adapter=imports.server_bridge_name, vlan_id=imports.server_vlan_id, firewall=False, cpu_type=pulumi.Output.concat("host"))
            .set_static_network(imports.server_ip)
            .set_initialization()
            .set_user_account('dorb', imports.public_key, "test1234")
            .build()
            )

      vm_ip = serverVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])

      dmzVM = (ProxmoxServerBuilder(imports.node_name, imports.template_id, provider)
            .set_name("dmz-vm")
            .set_server_name(pulumi.Output.concat("demezescu", "-vm"))
            .set_resources(cpu=imports.server_cpus, memory=imports.server_memory, storage=imports.server_storage, network_adapter=imports.dmz_bridge_name, vlan_id=imports.dmz_vlan_id, firewall=False, cpu_type=pulumi.Output.concat("host"))
            .set_static_network(imports.dmz_ip)
            .set_initialization()
            .set_user_account('dorb', imports.public_key, "test1234")
            .build())

      dmz_ip = dmzVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])
      return [(serverVM, vm_ip, 22, "server-vm"), (dmzVM, dmz_ip, 22, "dmz-vm")]
