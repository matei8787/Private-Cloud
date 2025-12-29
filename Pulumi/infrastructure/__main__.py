"""A Python Pulumi program"""

import pulumi
from imports import *
from Proxmox.server import ProxmoxServerBuilder
from Proxmox.provider import ProxmoxProviderBuilder
import pulumi_command as command
import yaml
import os

provider = ProxmoxProviderBuilder('proxmox-auth', True).set_token(pxm_token_id, pxm_token_secret).set_insecure(True).set_url(pxm_url).build()

serverVM = (ProxmoxServerBuilder('home', template_id, provider)
      .set_name("server")
      .set_server_name(server_name)
      .set_resources(cpu=server_cpus, memory=server_memory, storage=server_storage, network_adapter=server_bridge_name)
      .set_static_network(server_ip)
      .set_initialization()
      .set_user_account('dorb', public_key)
      .build()
      )

vm_ip = serverVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])

dmzVM = (ProxmoxServerBuilder('home', template_id, provider)
         .set_name("dmz")
         .set_server_name(pulumi.Output.concat("demezescu", "-vm"))
         .set_resources(cpu=server_cpus, memory=server_memory, storage=server_storage, network_adapter=dmz_bridge_name)
         .set_static_network(dmz_ip)
         .set_initialization()
         .set_user_account('dorb', public_key, "test1234")
         .build())

dmz_ip = dmzVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])

def create_ansible_inventory(machines: dict[str, list[dict[str, str]]]):
      #{ZONE: [{
      #     ansible_host: IP
      #     OPTIONAL: ansible_user: user, ansible_ssh_private_key_file: key_file
      # }]
      zones = {}
      for k, v in machines.items():
            i = 1
            zones[k] = {
                  "hosts": {}
            }
            for server in v:
                  node_name = f"{k}_node{str(i)}"
                  i += 1
                  args = {
                        'ansible_host': server['ansible_host']
                  }
                  if 'ansible_user' in server:
                        args['ansible_user'] = server['ansible_user']
                  if 'ansible_ssh_private_key_file' in server:
                        args['ansible_ssh_private_key_file'] = server['ansible_ssh_private_key_file']
                  zones[k]['hosts'].update({
                        node_name: args
                  })
      #zones: {Server:
      #           hosts:
      #                 server_nodeX:
      #                       ansible_server: IP ...}
      template_yaml = {
            'all': {
                  'children': zones,
            }
      }
      yaml_file = yaml.dump(template_yaml, sort_keys=False, default_flow_style=False)
      return f"cat <<EOF > ../../Ansible/inventory/inventory.yml\n{yaml_file}\nEOF\n"
      


create_inventory = command.local.Command("create-inventory",
                                            create=pulumi.Output.all(vm_ip, dmz_ip).apply(lambda arg: create_ansible_inventory({
                                                  'servers': [{
                                                        'ansible_host': arg[0],
                                                  }],
                                                  'dmz': [{
                                                        'ansible_host': arg[1],
                                                  }],
                                            })),
                                            opts=pulumi.ResourceOptions(depends_on=[serverVM, dmzVM]))


def wait_for_machine(ip: pulumi.Output, server_id, dependency, name):
      return command.local.Command(f'wait-for-port22-{name}',
                                         create=ip.apply(lambda x: f"while ! nc -z {x} 22; do\nsleep 1 \ndone\n echo 'port 22 is up'"),
                                         triggers=[server_id],
                                         opts = pulumi.ResourceOptions(depends_on=[dependency]))

def wait_for_ssh(ip, server_id, dependency, name):
      return command.remote.Command(f'wait-ssh-{name}',
                                    connection={
                                          'host': ip,
                                          'user': 'dorb',
                                          'agent_socket_path': os.environ.get("SSH_AUTH_SOCK"),
                                    },
                                    triggers=[server_id],
                                    create="echo 'SSH is ready!'",
                                    opts=pulumi.ResourceOptions(depends_on=[dependency]))

wait_for_machine_server = wait_for_machine(vm_ip, serverVM.id, create_inventory, "server")

wait_for_machine_dmz = wait_for_machine(dmz_ip, dmzVM.id, create_inventory, "dmz")

wait_for_ssh_server = wait_for_ssh(vm_ip, serverVM.id, wait_for_machine_server, "server")

wait_for_ssh_dmz = wait_for_ssh(dmz_ip, dmzVM.id, wait_for_machine_dmz, "dmz")

run_ansible = command.local.Command('run-ansible',
                                    create="ansible-playbook playbooks/site.yml",
                                    dir="../../Ansible",
                                    triggers=[serverVM.id, dmzVM.id],
                                    opts=pulumi.ResourceOptions(depends_on=[wait_for_ssh_server, wait_for_ssh_dmz]))


pulumi.export("serverIpAddress", vm_ip)
pulumi.export("dmzIpAddress", dmz_ip)
pulumi.export('serversAdminUser', 'dorb')
