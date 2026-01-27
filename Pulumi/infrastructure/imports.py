import pulumi


secrets = pulumi.StackReference("matei8787/configs/dev")

config = pulumi.Config()

try:
    run_option = config.require('runOption')
except Exception as e:
    pulumi.log.error(f"Missing required configuration: {e}")
    raise


def safe_get_output(name, default):
    aux_output = secrets.get_output(name)
    
    # If the output object is None (meaning the key wasn't exported at all),
    # we return a new Output that holds the default value.
    if aux_output is None:
        return pulumi.Output.from_input(default)

    # If the output object exists, we use .apply() to check if its *value* is None/empty 
    # and provide the default inside the async context.
    return aux_output.apply(lambda value: value if value is not None and value != "" else default)

#Get proxmox stuff
try:
    pxm_token_secret = secrets.require_output("proxmoxTokenSecret")
    pxm_token_id = secrets.require_output('proxmoxTokenId')
    pxm_url = secrets.require_output('proxmoxUrl')
    pxm_user = secrets.require_output("proxmoxUser")
    pxm_pass = secrets.require_output('proxmoxPass')
    global_domain = secrets.require_output('globalDnsDomain')
    node_name = secrets.require_output("proxmoxNodeName")
    public_key = secrets.require_output('sshPublicKey')
    gitlab_runner_key = secrets.require_output('gitlabRunnerKey')
    gitlab_server_key = secrets.require_output('gitlabServerKey')
    
except Exception as e:
    pulumi.log.error(f"Missing required proxmox configuration: {e}")
    raise


try:
    template_id = secrets.require_output('ubuntuClone')
except Exception as e:
    pulumi.log.error(f"Missing required ubuntu iso path: {e}")
    raise



server_name = safe_get_output("serverName", "ubuntu")
server_cpus = safe_get_output("ubuntuCpu", 2)
server_memory =safe_get_output("ubuntuMemory", 4096)
server_storage = safe_get_output("ubuntuStorage", 50) 
server_bridge_name = safe_get_output("lanBridgeName", "vmbr1")
dmz_bridge_name = safe_get_output("dmzBridgeName", "vmbr2")
dmz_ip = safe_get_output("dmzIpAddress", None)
server_ip = safe_get_output("ubuntuStaticIp", None)
server_vlan_id = safe_get_output("serverVlan", None)
dmz_vlan_id = safe_get_output("dmzVlan", None)