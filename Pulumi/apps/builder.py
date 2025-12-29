from typing import Union
import pulumi_docker as docker
from pulumi import Input, Output, ResourceOptions


class DockerAppBuilder:
    def __init__(self, name: str):
        self.name = name
        self.image_name = None
        self.envs = []
        self.ports = []
        self.volumes = []
        self.networks = []
        self.restart_policy = "unless-stopped"
        self.command = None
        self.opts = None
        self.entrypoint = None
    
    def set_restart(self, policy: str):
        self.restart_policy = policy
        return self
    
    def set_image(self, image: Input[str], tag: Input[str] = None):
        if tag:
            self.image_name = Output.concat(image, ":", tag)
        else:
            self.image_name = image
        return self
    
    def set_environment(self, envs: dict[str, Input[str]]):
        keys = list(envs.keys())
        values = list(envs.values())
        
        # Combine all values into one Output, then format them
        self.envs = Output.all(*values).apply(
            lambda resolved_values: [f'{keys[i]}={resolved_values[i]}' for i in range(len(keys))]
        )
        return self
    
    def add_env(self, key: str, val: Input[str]):
        val.apply(lambda x: self.envs.append(f'{key}={x}'))
        return self

    def add_volume(self, container_path: Input[str], host_path: Input[str], name: Input[str] = None, read_only: bool = False):
        if name:
            # Named Volume
            self.volumes.append(docker.ContainerVolumeArgs(
                volume_name=name,
                container_path=container_path,
                read_only=read_only,
            ))
        else:
            # Host Bind Mount
            self.volumes.append(docker.ContainerVolumeArgs(
                host_path=host_path,
                container_path=container_path,
                read_only=read_only,
            ))
        return self
    
    def set_ports(self, mapping: dict[int, int]):
        for k, v in mapping.items():
            if v is None:
                self.ports.append(docker.ContainerPortArgs(
                    internal=k,
                ))
            else:
                self.ports.append(docker.ContainerPortArgs(
                    internal=k,
                    external=v
                ))
        return self
    
    def add_port(self, internal: int, external: int):
        self.ports.append(docker.ContainerPortArgs(
            internal=internal,
            external=external
        ))
        return self
        
    def set_network(self, network_ids: list[Input[str]]):
        for id in network_ids:
            self.networks.append(id)
        return self
    
    def add_network(self, id):
        self.networks.append(id)
        return self
    
    def set_command(self, command: str):
        self.command = command
        return self
    
    def set_command(self, command: Union[str, list[str]]):
        if command is None:
            self.command = None
            return self
        self.command = command if isinstance(command, list) else command.split(" ")
        return self
    
    def add_command(self, cmd: str):
        self.command.append(cmd)
        return self
    
    def set_entrypoint(self, entrypoint: list[str]):
        self.entrypoint = entrypoint
        return self
    
    def add_entrypoint(self, entrypoint: str):
        self.entrypoint.append(entrypoint)
        return self
    def set_opts(self, opts: ResourceOptions):
        self.opts = opts
        return self
    
    def build(self):
        if not self.image_name:
            raise ValueError("Image name must be set before building")
        
        remote_image = docker.RemoteImage(
            f"{self.name}-image",
            name=self.image_name,
            keep_locally=True,
            opts=self.opts,
        )
        
        container = docker.Container(
            self.name,
            image=remote_image.repo_digest,
            name=self.name,
            envs=self.envs,
            ports=self.ports,
            volumes=self.volumes,
            networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=n) for n in self.networks],
            restart=self.restart_policy,
            command=self.command,
            entrypoints=self.entrypoint,
            opts=self.opts,
        )
        return container
    

class DockerImageBuilder:
    def __init__(self, name: str):
        self.name = name
        self.platform = 'linux/amd64'
        self.context = None
        self.dockerfile = "Dockerfile"
        self.image_name = None
        self.registry = None
        
    def set_platform(self, platform: str):
        self.platform = platform
        return self
    
    def set_context(self, folder_path: Input[str]):
        self.context = folder_path
        return self
    
    def set_target_image(self, image_name: Input[str]):
        self.image_name = image_name
        return self

    def set_registry(self, server: Input[str], username : Input[str], password : Input[str]):
        self.registry = docker.RegistryArgs(
            server=server,
            username=username,
            password=password
        )
        return self
    
    def build(self) -> docker.Image:
        """
        Builds locally and pushes to the registry.
        Returns the Image resource.
        """
        if not self.image_name or not self.context:
            raise ValueError("Target image name and context are required.")
        
        # This resource runs on YOUR LAPTOP (default provider), not the remote VM.
        image = docker.Image(
            self.name,
            build=docker.DockerBuildArgs(
                context=self.context,
                dockerfile=self.context.apply(lambda x: f"{x}/{self.dockerfile}"),
                platform="linux/amd64", # Important if you are on an Apple Silicon Mac!
            ),
            image_name=Output.concat(self.registry.username, '/', self.image_name),
            registry=self.registry,
            skip_push=False
        )
        return image