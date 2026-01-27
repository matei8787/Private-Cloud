import pulumi

config = pulumi.Config()

# --- A. Read the Configurations (Non-Secret) ---
# Use .require() for mandatory settings
try:
    proxmox_url = config.require('proxmoxUrl')
    proxmox_token_id = config.require('proxmoxTokenId')
    proxmox_lan_bridge = config.require("lanBridgeName")
    dmz_lan_bridge = config.require("dmzBridgeName")
    proxmox_user = config.require("proxmoxUser")
    app_db_name = config.require("appSqlName")
    app_db_engine = config.require("appSqlEngine")
    ubuntu_iso = config.require("ubuntuFileId")
    ubuntu_clone = config.require("ubuntuTemplateId")
    proxmox_node_name = config.require("proxmoxNodeName")
    public_key = config.require('sshPublicKey')
    pfs_host = config.require("pfsHost")
    vault_prtocol = config.require('vaultProtocol')
    docker_user = config.require('dockerUser')
    traefik_ovpn_host = config.require('dmzVpnHost')
    traefik_ovpn_port = config.require('dmzVpnPort')
    dmz_ip_address = config.require('dmzIpAddress')
    gitlab_runner_key = config.require('gitlabRunnerKey')
    gitlab_server_key = config.require('gitlabServerKey')
    
    # Use .get() for optional settings, providing a default if not set
    appDebug = config.get("appDebug") or "False"
    dmz_vlan_id = config.get("dmzVlan") or None
    server_vlan_id = config.get("serverVlan") or None
    management_vlan_id = config.get("managementVlan") or None
    hello_debug = config.get('helloDebug') or "False"
    app_log_folder = config.get('logFolder') or '/app/log'
    app_redis_host = config.get('redisHost') or 'redis'
    app_redis_port = config.get('redisPort') or 6379
    vault_web_socket = config.get('vaultWebSocket') or 'true'
    vault_sub_domain = config.get('vaultSubDomain') or 'vault'
    ubuntu_cpus = config.get("ubuntuCpu") or 1
    ubuntu_memory = config.get("ubuntuMemory") or 4096
    ubuntu_storage = config.get("ubuntuStorage") or 50
    postgres_user = config.get("postgresUser") or 'admin'
    app_sql_port = config.get("appSqlPort") or 5432
    postgres_hostname = config.get("appSqlHost") or "postgres-db"
    machines_fqdn = config.get('globalDnsDomain') or "dorb.local "
    ubuntu_static_ip = config.get('ubuntuStaticIp') or None
    
except Exception as e:
    # A simple error message if mandatory config is missing
    pulumi.log.error(f"Missing required configuration: {e}")
    # Prevent deployment if crucial config is missing
    raise

# --- B. Read the Secrets (Encrypted Values) ---
# Use .require_secret() for sensitive data set with 'pulumi config set --secret'
try:
    proxmox_password = config.require_secret("proxmoxPass")
    proxmox_token_secret = config.require_secret('proxmoxTokenSecret')
    postgres_pass = config.require_secret('postgresPass')
    app_secret = config.require_secret('appSecret')
    vpn_pfs_key = config.require_secret('pfsKey')
    vpn_pfs_test_CA = config.require_secret('pfsTestCA')
    vpn_verify_ssl = config.require_secret('verifySSL')
    vpn_allowed_hosts = config.require_secret('allowedHosts')
    hello_allowed_hosts = config.require_secret('helloAllowedHosts')
    docker_secret = config.require_secret('dockerSecret')
except Exception as e:
    # A simple error message if mandatory config is missing
    pulumi.log.error(f"Missing required secret configuration: {e}")
    # Prevent deployment if crucial config is missing
    raise

# --- C. Export the Contract ---
# This step publishes these values (secrets remain encrypted) to the stack's state,
# allowing the StackReference in Projects 1 and 2 to retrieve them.

# Infrastructure/Security Config for Project 1
pulumi.export('proxmoxUrl', proxmox_url)
pulumi.export('proxmoxTokenId', proxmox_token_id)
pulumi.export('proxmoxTokenSecret', proxmox_token_secret) 
pulumi.export('proxmoxNodeName', proxmox_node_name)
pulumi.export('lanBridgeName', proxmox_lan_bridge)
pulumi.export('ubuntuCpus', ubuntu_cpus)
pulumi.export('ubuntuMemory', ubuntu_memory)
pulumi.export('ubuntuStorage', ubuntu_storage)
pulumi.export('ubuntuFileId', ubuntu_iso)
pulumi.export('ubuntuClone', ubuntu_clone)
pulumi.export('globalDnsDomain', machines_fqdn)
pulumi.export('proxmoxUser', proxmox_user)
pulumi.export('proxmoxPass', proxmox_password)
pulumi.export('ubuntuStaticIp', ubuntu_static_ip)
pulumi.export('sshPublicKey', public_key)
pulumi.export('dmzBridgeName', dmz_lan_bridge)
pulumi.export('dmzIpAddress', dmz_ip_address)
pulumi.export('dmzVlan', dmz_vlan_id)
pulumi.export('serverVlan', server_vlan_id)
pulumi.export('managementVlan', management_vlan_id)

# Application/Service Config for Project 2
pulumi.export('postgresPass', postgres_pass)
pulumi.export('postgresUser', postgres_user)
pulumi.export('ovpnSqlEngine', app_db_engine)
pulumi.export('ovpnSqlName', app_db_name)
pulumi.export('ovpnSecret', app_secret)
pulumi.export('ovpnDebug', appDebug)
pulumi.export('postgresHostname', postgres_hostname)
pulumi.export('postgresPort', app_sql_port)
pulumi.export('ovpnPfsKey', vpn_pfs_key)
pulumi.export('ovpnPfsHost', pfs_host)
pulumi.export('ovpnPfsTestCA', vpn_pfs_test_CA)
pulumi.export('ovpnVerifySSL', vpn_verify_ssl)
pulumi.export('ovpnAllowedHosts', vpn_allowed_hosts)
pulumi.export('ovpnLogFolder', app_log_folder)
pulumi.export('redisHost', app_redis_host)
pulumi.export('redisPort', app_redis_port)
pulumi.export('vaultWebSocket', vault_web_socket)
pulumi.export('vaultSubDomain', vault_sub_domain)
pulumi.export('vaultProtocol', vault_prtocol)
pulumi.export('helloAllowedHosts', hello_allowed_hosts)
pulumi.export('helloDebug', hello_debug)
pulumi.export('dockerPass', docker_secret)
pulumi.export('dockerUser', docker_user)
pulumi.export('dmzVpnHost', traefik_ovpn_host)
pulumi.export('dmzVpnPort', traefik_ovpn_port)

# Other exports
pulumi.export('gitlabRunnerKey', gitlab_runner_key)
pulumi.export('gitlabServerKey', gitlab_server_key)