"""A Python Pulumi program"""

from email.policy import default
from logging import config
import pulumi
from Proxmox.provider import ProxmoxProviderBuilder
from Proxmox.server import ProxmoxServerBuilder




# Get configs
cfg = {}
def get_config():
    global cfg
    secrets = pulumi.Config()
    def safe_get_output(name, default):
        aux_output = secrets.get(name)
        
        # If the output object is None (meaning the key wasn't exported at all),
        # we return a new Output that holds the default value.
        if aux_output is None:
            return pulumi.Output.from_input(default)

        # If the output object exists, we use .apply() to check if its *value* is None/empty 
        # and provide the default inside the async context.
        return aux_output.apply(lambda value: value if value is not None and value != "" else default)

    try:
        pxm_token_secret = secrets.require_secret("proxmoxTokenSecret")
        pxm_token_id = secrets.require_secret('proxmoxTokenId')
        pxm_url = secrets.require_secret('proxmoxUrl')
        pxm_user = secrets.require_secret("proxmoxUser")
        pxm_pass = secrets.require_secret('proxmoxPass')
        public_key = secrets.require_secret('sshPublicKey')
    except Exception as e:
        pulumi.log.error(f"Missing required proxmox configuration: {e}")
        raise
    
    cfg['server_name'] = pulumi.Output.from_input("StreamingVM") 
    cfg['server_cpus'] = pulumi.Output.from_input('8')
    cfg['server_memory'] = pulumi.Output.from_input('10240')
    cfg['server_storage'] = pulumi.Output.from_input('32')
    cfg['server_bridge_name'] = pulumi.Output.from_input('service')
    cfg['server_ip'] = pulumi.Output.from_input('10.69.93.5/24')
    cfg['server_vlan_id'] = pulumi.Output.from_input('93')
    cfg['pxm_token_secret'] = pxm_token_secret
    cfg['pxm_token_id'] = pxm_token_id
    cfg['pxm_url'] = pxm_url
    cfg['pxm_user'] = pxm_user
    cfg['pxm_pass'] = pxm_pass
    cfg['public_key'] = public_key
    
def create_proxmox_provider():
    provider = ProxmoxProviderBuilder('proxmox-auth', True).set_token(cfg['pxm_token_id'], cfg['pxm_token_secret']).set_insecure(True).set_url(cfg['pxm_url']).build()
    return provider

def create_streaming_server(provider: ProxmoxProviderBuilder):
    server = (ProxmoxServerBuilder('pve', 9000, provider)
            .set_name("streaming-server")
            .set_server_name(cfg['server_name'])
            .set_resources(cpu=cfg['server_cpus'], memory=cfg['server_memory'], storage=cfg['server_storage'], network_adapter=cfg['server_bridge_name'], vlan_id=cfg['server_vlan_id'], firewall=False, cpu_type=pulumi.Output.concat("host"))
            .set_static_network(cfg['server_ip'])
            .set_initialization()
            .set_user_account('dorb', cfg['public_key'])
            .build()
            )
    return server

def main():
    get_config()
    proxmox_provider = create_proxmox_provider()
    streaming_server = create_streaming_server(proxmox_provider)

main()
    
    