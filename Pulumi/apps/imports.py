import pulumi

secrets = pulumi.StackReference("matei8787/configs/dev")

def safe_get(secret: pulumi.StackReference, field: pulumi.Input[str], default):
    var = secret.get_output(field)
    if not var:
        var = default
    return var
    



pg_host = safe_get(secrets, 'postgresHostname', 'postgres-db')
pg_port = safe_get(secrets, "postgresPort", 5432)

# Required Configs
try:
    pg_user = secrets.require_output('postgresUser')
    pg_pass = secrets.require_output('postgresPass')
    vpn_db_engine = secrets.require_output('ovpnSqlEngine')
    vpn_secret = secrets.require_output('ovpnSecret')
    pfs_host = secrets.require_output('ovpnPfsHost')
    pfs_key = secrets.require_output('ovpnPfsKey')
    pfs_test_ca = secrets.require_output('ovpnPfsTestCA')
    vpn_verify_ssl = secrets.require_output('ovpnVerifySSL')
    global_domain = secrets.require_output('globalDnsDomain')
    vpn_allowed_hosts = secrets.require_output('ovpnAllowedHosts')
    vault_subdomain = secrets.require_output('vaultSubDomain')
    vault_protocol = secrets.require_output('vaultProtocol')
    hello_allowed_hosts = secrets.require_output('helloAllowedHosts')
    hello_debug = secrets.require_output('helloDebug')
    docker_pass = secrets.require_output('dockerPass')
    docker_user = secrets.require_output('dockerUser')
    traefik_ovpn_host = secrets.require_output('dmzVpnHost')
    traefik_ovpn_port = secrets.require_output('dmzVpnPort')
except Exception as e:
    pulumi.log.error(e)
    raise ValueError("Required output not found")



vpn_env = {
    'debug': safe_get(secrets, 'ovpnDebug', "False") == "True",
    'django_secret': vpn_secret,
    'sql': {
        'name': safe_get(secrets, 'ovpnSqlName', "vpn_provisioner"),
        'port': pg_port,
        'engine': vpn_db_engine,
        'host': pg_host,
        'user': pg_user,
        'pass': pg_pass,
    },
    'pfSense': {
        'host': pfs_host,
        'key': pfs_key,
        'test_CA': pfs_test_ca,
    },
    'log_folder': safe_get(secrets, 'ovpnAllowedHosts', '/app/log'),
    'allowed_hosts': vpn_allowed_hosts,
    'verify_ssl': vpn_verify_ssl,
    'redis': {
        'host': safe_get(secrets, 'redisHost', 'redis'),
        'port': safe_get(secrets, 'redisPort', 6379),
    }
}


vaultwarden_env = {
    'websocket_enabled': safe_get(secrets, 'vaultWebSocket', 'true'),
    'domain': pulumi.Output.concat(vault_protocol, vault_subdomain, '.', global_domain)
}

postgres_env = {
    'postgres_user': pg_user,
    'postgres_password': pg_pass,
}

hello_env = {
    'debug': hello_debug,
    'allowed_hosts': hello_allowed_hosts,
    'secret_key': vpn_secret,
}


infra_secrets = pulumi.StackReference('matei8787/infrastructure/dev')

try:
    server_ip = infra_secrets.require_output('serverIpAddress')
    server_user = infra_secrets.require_output('serversAdminUser')
    dmz_ip = infra_secrets.require_output('dmzIpAddress')
except Exception as e:
    pulumi.log.error(e)
    raise ValueError("Required Infrastructure Output not found")




traefik_env = {
    'openvpn_host': traefik_ovpn_host,
    'openvpn_port': traefik_ovpn_port,
    'openvpn_ip': server_ip,
}