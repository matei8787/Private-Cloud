"""A Python Pulumi program"""

import pulumi
from pulumi import ResourceOptions
from imports import *
from create import *


def remote_docker_provider(name: str, user: pulumi.Input[str], address: pulumi.Input[str]):
    return docker.Provider(name,
                           host=pulumi.Output.concat('ssh://', user, '@', address))


server_prov = remote_docker_provider('docker-prov', server_user, server_ip)
dmz_prov = remote_docker_provider('docker-prov-dmz', server_user, dmz_ip)
internal_network = docker.Network('internal-network',
                                  opts=pulumi.ResourceOptions(provider=server_prov))
class Postgress:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str], postgres_env):
        self.volume = docker.Volume('postgres_data',
                                opts=pulumi.ResourceOptions(provider=prov))

        self.img = create_image('postgres-db', 
                                    './postgres/', 
                                    'postgres-custom', 
                                    "docker.io", 
                                    docker_user, 
                                    docker_pass)
        self.app = create_app('postgres-db', 
                                    self.img,
                                    postgres_env, 
                                    {
                                        self.volume: {
                                            'container_path': '/var/lib/postgresql/data',
                                        }
                                    },
                                    [internal_network.id],
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]))

class Redis:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str]):
        self.volume = docker.Volume('redis_data',
                                    opts=pulumi.ResourceOptions(provider=prov))

        self.img = create_image('redis', 
                                    './redis/', 
                                    'redis-custom', 
                                    "docker.io", 
                                    docker_user, 
                                    docker_pass,)
        self.app = create_app('redis', 
                                    self.img,
                                    {}, 
                                    {
                                        self.volume: {
                                            'container_path': '/data',
                                        }
                                    },
                                    [internal_network.id],
                                    ports={6379:None},
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]))

class VPNApp:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str], vpn_env):
        self.static_volume = docker.Volume('vpn_static',
                                            opts=pulumi.ResourceOptions(provider=prov))
        self.media_volume = docker.Volume('vpn_media',
                                           opts=pulumi.ResourceOptions(provider=prov))
        self.img = create_image('vpn-provisioner', 
                                    './vpn_provisioner', 
                                    'vpn-provisioner-custom', 
                                    "docker.io", 
                                    docker_user, 
                                    docker_pass,)
        self.app = create_app('vpn-provisioner', 
                                    self.img,
                                    vpn_env, 
                                    {
                                        self.static_volume: {
                                            'container_path': '/usr/share/nginx/html/ovpn/staticfiles',
                                        },
                                        self.media_volume: {
                                            'container_path': '/usr/share/nginx/html/ovpn/mediafiles',
                                        }
                                    },
                                    [internal_network.id],
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]),
                                    ports={8000:None})
        
class HelloApp:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str], hello_env):
        self.static_volume = docker.Volume('hello_static',
                                            opts=pulumi.ResourceOptions(provider=prov))
        self.img = create_image('hello-app',
                                    './hello_app',
                                    'hello-app-custom',
                                    "docker.io",
                                    docker_user,
                                    docker_pass,)
        self.app = create_app('hello', 
                                    self.img,
                                    hello_env, 
                                    {
                                        self.static_volume: {
                                            'container_path': '/usr/share/nginx/html/hello/staticfiles',
                                        }
                                    },
                                    [internal_network.id],
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]),
                                    ports={8000:None})
        
class VaultApp:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str], vault_env):
        self.data_volume = docker.Volume('vault_data',
                                            opts=pulumi.ResourceOptions(provider=prov))
        self.img = create_image('vaultwarden',
                                    './vaultwarden',
                                    'vaultwarden-custom',
                                    "docker.io",
                                    docker_user,
                                    docker_pass,)
        self.app = create_app('vaultwarden', 
                                    self.img,
                                    vault_env, 
                                    {
                                        self.data_volume: {
                                            'container_path': '/data',
                                        }
                                    },
                                    [internal_network.id],
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]),
                                    ports={80:None})
class Nginx:
    CERTS_PATH='/etc/pki/certs'
    def __init__(
        self, 
        prov: docker.Provider, 
        docker_user: pulumi.Input[str], 
        docker_pass: pulumi.Input[str], 
        shared_volumes: list, 
        host_cert_path: str 
    ):
        volume_config = {}
        
        # 1. Map the App Shared Volumes (Read-Only)
        for vol_resource, target_path in shared_volumes:
            volume_config[vol_resource] = {
                'container_path': target_path,
                'read_only': True 
            }

        # 2. Map the Certificates (Read-Only Bind Mount)
        volume_config["ssl_certs"] = {
            'host_path': host_cert_path,
            'container_path': Nginx.CERTS_PATH, 
            'type': 'bind',
            'read_only': True
        }

        self.img = create_image('nginx', 
                                './nginx', 
                                'nginx-custom', 
                                "docker.io", 
                                docker_user, 
                                docker_pass)
        
        # Dependencies: Image + Shared App Volumes
        deps = [self.img] + [v[0] for v in shared_volumes]

        self.app = create_app(
            'nginx', 
            self.img,
            {}, 
            volume_config,
            [internal_network.id],
            opts=ResourceOptions(provider=prov, depends_on=deps),
            ports={80: 80, 443: 443} 
        )


class Servers:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str]):
        self.postgres = Postgress(prov, docker_user, docker_pass, postgres_env)
        self.redis = Redis(prov, docker_user, docker_pass)
        self.vpn_app = VPNApp(prov, docker_user, docker_pass, vpn_env)
        self.hello_app = HelloApp(prov, docker_user, docker_pass, hello_env)
        self.vault_app = VaultApp(prov, docker_user, docker_pass, vaultwarden_env)

        nginx_shares = [
            (self.vpn_app.static_volume, '/usr/share/nginx/html/ovpn/staticfiles'),
            (self.vpn_app.media_volume,  '/usr/share/nginx/html/ovpn/mediafiles'),
            (self.hello_app.static_volume, '/usr/share/nginx/html/hello/staticfiles')
        ]
        host_cert_path = '/etc/pki/certs'
        self.nginx = Nginx(prov, docker_user, docker_pass, nginx_shares, host_cert_path=host_cert_path)



class Traefik:
    CERT_PATH='/certs'
    def __init__(
        self, 
        prov: docker.Provider, 
        docker_user: pulumi.Input[str], 
        docker_pass: pulumi.Input[str], 
        host_cert_path: str  
    ):
        self.img = create_image('traefik', 
                                './traefik', 
                                'traefik-custom', 
                                "docker.io", 
                                docker_user, 
                                docker_pass)
        
        # Volume Mapping for Certs
        volumes = {
            "ssl_certs": {
                'host_path': host_cert_path,
                'container_path': Traefik.CERT_PATH, 
                'type': 'bind',
                'read_only': True,
            },
        }

        self.app = create_app('traefik', 
                                    self.img,
                                    traefik_env, 
                                    volumes, # Pass the volume map
                                    [], # No internal network for DMZ Traefik
                                    opts=ResourceOptions(provider=prov, depends_on=[self.img]),
                                    # Use Integers!
                                    ports={80: 80, 443: 443} 
        )
        

class DMZ:
    def __init__(self, prov: docker.Provider, docker_user: pulumi.Input[str], docker_pass: pulumi.Input[str]):
        host_cert_path = '/certs'
        self.traefik = Traefik(prov, docker_user, docker_pass, host_cert_path=host_cert_path)


servers = Servers(server_prov, docker_user, docker_pass)
dmz = DMZ(dmz_prov, docker_user, docker_pass)