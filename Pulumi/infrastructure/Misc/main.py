import os
import imports as imports
import pulumi
from Proxmox.provider import ProxmoxProviderBuilder
from Proxmox.server import ProxmoxServerBuilder
import yaml
import pulumi_command as command


def create_vms(provider=None):
      serverVM = (ProxmoxServerBuilder(pulumi.Output.concat("pv", "e"), imports.template_id.apply(lambda x: int(x)), provider)
                  .set_name("Gitlab-Server") 
                  .set_server_name(pulumi.Output.concat("gitlab"))
                  .set_resources(cpu=pulumi.Output.concat("4"), memory=pulumi.Output.concat("10240"), storage=pulumi.Output.concat("100"), network_adapter=imports.server_bridge_name, vlan_id=imports.server_vlan_id, firewall=False, cpu_type=pulumi.Output.concat("host"))
                  .set_static_network(pulumi.Output.concat("10.69.10.", "6/24"))
                  .set_initialization()
                  .set_user_account('dorb', imports.gitlab_server_key)
                  .build()
                  )
      gitlab_server_ip = serverVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])
      runnerVM = (ProxmoxServerBuilder(pulumi.Output.concat("pve", "-", "worker"), imports.template_id.apply(lambda x: int(x)+1), provider)
                  .set_name("Gitlab-Runner") 
                  .set_server_name(pulumi.Output.concat("gitlab-runner"))
                  .set_resources(cpu=pulumi.Output.concat("3"), memory=pulumi.Output.concat("6144"), storage=pulumi.Output.concat("50"), network_adapter=imports.server_bridge_name, vlan_id=imports.server_vlan_id, firewall=False, cpu_type=pulumi.Output.concat("host"))
                  .set_static_network(pulumi.Output.concat("10.69.10.", "7/24"))
                  .set_initialization()
                  .set_user_account('dorb', imports.gitlab_runner_key)
                  .build()
                  )
      runner_ip = runnerVM.initialization.apply(lambda x: f"{x['ip_configs'][0]['ipv4']['address']}".split('/')[0])
      return [(serverVM, gitlab_server_ip, 22, "gitlab-server"), (runnerVM, runner_ip, 22, "gitlab-runner")]

