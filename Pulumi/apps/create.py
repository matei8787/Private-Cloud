import pulumi
from pulumi import Input, Output
import pulumi_docker as docker
from builder import DockerAppBuilder, DockerImageBuilder
from typing import Union

def create_image(name: str, context: Input[str], target_image: Input[str], server_reg: Input[str], user_reg: Input[str], pass_reg: Input[str]):
    context = Output.from_input(context)
    target_image = Output.from_input(target_image)
    server_reg = Output.from_input(server_reg)
    user_reg = Output.from_input(user_reg)
    pass_reg = Output.from_input(pass_reg)
    return (DockerImageBuilder(name)
            .set_context(context)
            .set_target_image(target_image)
            .set_registry(server_reg, user_reg, pass_reg)
            .build())

def create_app(name: str, image: docker.Image, envs: dict[str, Union[Input[str], dict[str, Input[str]]]], volumes: dict[str, Union[Input[str], dict[str, Input[str]]]], networks: list, opts: pulumi.ResourceOptions, ports: dict[int, int] = {"5432":"5432"}, command: list[str] = None, entrypoint: list[str] = None):
    app = (DockerAppBuilder(name)
              .set_image(image.repo_digest)
              .set_network(networks)
              .set_ports(ports)
              .set_command(command)
              .set_entrypoint(entrypoint)
              .set_opts(opts))
    for vol in volumes:
        vol_name = vol.name if hasattr(vol, 'name') else vol
        val = volumes[vol]
        
        if isinstance(val, (Output, str)):
            # It's a named volume. Pass vol_name as 'name', NOT 'host_path'
            app.add_volume(container_path=val, host_path=None, name=vol_name)
        elif isinstance(val, dict):
            if 'type' in val and val['type'] == 'bind':
                app.add_volume(
                    container_path=val.get('container_path'), 
                    host_path=val.get('host_path'),
                    read_only=val.get('read_only', False),
                )
            else:
                container_path = val.get('container_path')
                host_path = val.get('host_path')
                read_only = val.get('read_only', False)
                app.add_volume(
                    container_path=container_path, 
                    host_path=host_path, # Can be None for named volumes
                    name=vol_name, 
                    read_only=read_only
                )

    good_envs = {}
    for k in envs:
        name=k.upper()
        if isinstance(envs[k], dict):
            for key in envs[k]:
                #name_key:envs[k][key]
                good_envs[name + "_" + key.upper()] = envs[k][key]
        else:
            good_envs[name] = envs[k]

    app.set_environment(good_envs)

    return app.build()
