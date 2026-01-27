from typing import Optional
from abstract.server import ServerBuilderInterface
import pulumi_proxmoxve as proxmox
from pulumi import Input, ResourceOptions, Output

RANDOM = "heairwouthwoieau392178469127wsieurohawerti78qyh324i5un"

class ProxmoxServerBuilder(ServerBuilderInterface):
    def __init__(self, node_name: Output[str], template_id: Output[int], provider=None):
        self.node = node_name
        self.template_id = template_id
        self.opts = {}
        if provider:
            self.opts['provider'] = provider
        
        
    def set_name(self, name: str):
        self.name = name
        return self
    
    def set_server_name(self, server_name: Output[str]):
        self.server_name = server_name
        return self
    
    def set_resources(self, cpu: Output[int],
                      memory: Output[int], 
                      storage: Output[int], 
                      network_adapter: Output[str], 
                      
                      storage_pool: Output[str] = None,
                      vlan_id: Optional[Output[int]] = None,
                      sockets: Optional[Output[int]] = None, cpu_type: Optional[Output[str]] = None,
                      storage_interface: Optional[Output[str]] = None, storage_format: Optional[Output[str]] = None, isssd: Optional[Output[bool]] = None,
                      more_network_adapters: Optional[list[tuple[Output[str], Output[str]]]] = None,
                      firewall: Optional[bool] = True):
        
        # 1. CPU Logic (Using the inherited helper)
        if not sockets:
            self.cpu = {'cores': cpu.apply(lambda x: int(x)), 'sockets': 1}
        else:
            self.cpu = {
                # Look how clean this is now:
                'cores': cpu.apply(lambda x: int(x)),
                'sockets': sockets.apply(lambda x: int(x)),
            }
        if cpu_type:
            self.cpu['type'] = cpu_type.apply(lambda x: f"{x}")


        # 2. Memory Logic
        self.memory = {'dedicated': memory.apply(lambda x: int(x))}


        # 3. Storage Logic (FIXED)
        # If no pool is provided, default to 'local-zfs' or raise error
        self.target_storage_pool = storage_pool if storage_pool else Output.from_input("local-zfs")

        if not storage_format or not storage_interface or not isssd:
            self.storage_disks = [{
                'interface': 'scsi0', 
                'file_format': 'raw', 
                'size': storage, 
                'ssd': True,
                'datastore_id': self.target_storage_pool 
            }]
        else:
            self.storage_disks = [{
                'interface': storage_interface.apply(lambda x: f"{x}"),
                'file_format': storage_format.apply(lambda x: f"{x}"),
                'size': storage.apply(lambda x: int(x)),
                'ssd': isssd.apply(lambda x: bool(x)),
                'datastore_id': self.target_storage_pool 
            }]

        # 4. Network Logic 
        self.network_devices = []
        
        # Base config
        primary_net = {
            'bridge': network_adapter.apply(lambda x: f"{x}"),
            'model': 'virtio',
            'firewall': firewall,
        }
        
        # Inject VLAN ID if provided
        if vlan_id:
            primary_net['vlan_id'] = vlan_id.apply(lambda x: int(x))

        self.network_devices.append(primary_net)
        
        # Handling secondary adapters (Optional: You might want to add VLAN support here too later)
        if more_network_adapters:
            for adapter in more_network_adapters:
                bridge = adapter[0].apply(lambda x: f"{x}")
                model = adapter[1].apply(lambda x: f"{x}")
                # You can extend this tuple logic later if secondary NICs need VLANs
                self.network_devices.append({
                    "bridge": bridge,
                    "model": model,
                })

        return self
    
    
    def set_static_network(self, cidr: Output[str]):
        self.dns = {}
        self.ip_configs = []
        gateway = cidr.apply(lambda x: '.'.join(x.split('.')[:-1]) + '.1')
        self.dns['servers'] = [gateway, '8.8.8.8', '1.1.1.1']
        self.ip_configs.append({
            'ipv4': {
                'address': cidr.apply(lambda x: x),
                'gateway': gateway,
            },
        })
        
        return self
    
    def set_user_account(self, username: Output[str], ssh_keys, password: Optional[str] = None):
        if isinstance(ssh_keys, Output):
            keys = [ssh_keys]
        elif isinstance(ssh_keys, list):
            keys = ssh_keys
        else:
            raise ValueError(f"SSH Key(s) must be either an Output[str] or a list of Output[str], got {type(ssh_keys)}")
        if password:
            self.user_account = {
                'username': username,
                'keys': keys,
                'password': password,
            }
        else:
            self.user_account = {
                'username': username,
                'keys': keys,
            }
        
        return self
        
    def set_initialization(self, initialization: Optional[dict] = {'type': 'nocloud'}):
        self.initialization = {}
        defaults = [
            ('type', 'nocloud'),
            ('dns', {
                'servers': ['8.8.8.8', '1.1.1.1'],
            }),
            ('ip_configs', [{
                'ipv4': {'address': 'dhcp'},
            },]),
        ]
        
        for d in defaults:
            if hasattr(self, d[0]):
                self.initialization[d[0]] = self.__getattribute__(d[0])
                continue
            if d[0] in initialization:
                self.initialization[d[0]] = initialization[d[0]]
                continue
            self.initialization[d[0]] = d[1]
        
        return self
    
    def set_opts(self, provider=None, **kwargs):
        if provider:
            self.opts['provider'] = provider
        elif 'provider' not in self.opts:
            raise ValueError("provider is a required property.")
        
        self.opts.update(kwargs)
        return self
    
    def build(self, on_boot=False, os_type='l26', reboot_after_update=False):
        if not self.user_account:
            raise ValueError("User account Not Set")
        self.initialization['user_account'] = self.user_account
        
        if hasattr(self, 'target_storage_pool'):
             self.initialization['datastore_id'] = self.target_storage_pool
        else:
             self.initialization['datastore_id'] = Output.from_input("local-zfs")
        
        opts = ResourceOptions(
            provider = self.opts.get('provider'),
            depends_on=self.opts.get('depends_on'),
            protect=self.opts.get('protect'),
            ignore_changes=self.opts.get('ignore_changes'),
        )
        
        return proxmox.vm.VirtualMachine(
            self.name,
            node_name=self.node,
            clone={
                'node_name': self.node,
                'vm_id': self.template_id,
                'full': True,
            },
            cpu=self.cpu,
            disks=self.storage_disks,
            memory=self.memory,
            name=self.server_name.apply(lambda x: f"{x}-Server"),
            network_devices=self.network_devices,
            on_boot=on_boot,
            operating_system = {
                'type': os_type,
            },
            reboot_after_update=reboot_after_update,
            initialization=self.initialization,
            opts=opts,
        )