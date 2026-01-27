import random
import yaml
import Basic.main as proj
import imports as imports
from Proxmox.provider import ProxmoxProviderBuilder
import Misc.main as misc
import pulumi_command as command
import pulumi
import os 

def make_proxmox_provider():
    provider = ProxmoxProviderBuilder('proxmox-auth', True).set_token(imports.pxm_token_id, imports.pxm_token_secret).set_insecure(True).set_url(imports.pxm_url).build()
    return provider
def generate_inventory_content(resolved_machines):
    inventory_machines = {"all":{"children":{}}}
    
    for name, ip, port in resolved_machines:
        if "dmz-vm" in name.lower():
            zone = "dmz"
        elif "server-vm" in name.lower():
            zone = "servers"
        else:
            zone = "gitlab"
            
        if zone not in inventory_machines["all"]["children"]:
            inventory_machines["all"]["children"][zone] = {
                "hosts": {}
            }
        
        inventory_machines['all']['children'][zone]['hosts'][name] = {}
        
        inventory_machines["all"]["children"][zone]['hosts'][name].update({
            'ansible_host': ip,
            'ansible_port': port,
        })

    # Return the actual YAML string
    return yaml.dump(inventory_machines, sort_keys=False, default_flow_style=False)
   
def create_commands(machines):
    
    vms = []
    for m in machines:
        vm, ip, port, name = m
        vms.append(pulumi.Output.all(name, ip, port))
    
    resolved_vms = pulumi.Output.all(*vms)
    inventory_yml = resolved_vms.apply(generate_inventory_content)
    
    create_inventory = command.local.Command("create-inventory",
                                            create=inventory_yml.apply(lambda x: f"cat <<EOF > ../../Ansible/inventory/inventory.yml\n{x}\nEOF"),
                                            opts=pulumi.ResourceOptions(depends_on=[m[0] for m in machines]))


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
        
    dependencies = []
    for m in machines:
        
        vm, ip, port, name = m
        
        wait_for_machine_vm = wait_for_machine(ip, vm.id, create_inventory, name)
        wait_for_ssh_vm = wait_for_ssh(ip, vm.id, wait_for_machine_vm, name)
        dependencies.append(wait_for_ssh_vm)

    run_ansible = command.local.Command('run-ansible',
                                        create="ansible-playbook playbooks/site.yml",
                                        dir="../../Ansible",
                                        triggers=[m[0].id for m in machines],
                                        opts=pulumi.ResourceOptions(depends_on=dependencies))


def export_outputs(machines):
    for m in machines:
        _, ip, _, name = m
        if "dmz-vm" == name.lower():
            pulumi.export("dmzIpAddress", ip)
        elif "server-vm" == name.lower():
            pulumi.export("serverIpAddress", ip)
        else:
            pulumi.export(name + 'IpAddress', ip)
    
    pulumi.export("serversAdminUser", "dorb")
            


def main():
    prov = make_proxmox_provider()
    proj_machines = proj.create_vms(prov)
    misc_machines = misc.create_vms(prov)
    all_machines = proj_machines + misc_machines
    create_commands(all_machines)
    export_outputs(all_machines)
        

if __name__ == "__main__":
    main()