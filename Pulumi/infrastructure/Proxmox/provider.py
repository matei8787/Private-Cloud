from abstract.provider import ProviderBuilderInterface
from pulumi_proxmoxve import provider
from pulumi import Input, Output

class ProxmoxProviderBuilder(ProviderBuilderInterface):
    
    def __init__(self, name='proxmox-auth', insecure=False):
        self.name = name
        self.insecure = insecure
    
    def set_url(self, url: Input[str]):
        self.url = url
        return self
    
    def set_token(self, tokenID: Input[str], tokenSecret: Input[str]):
        self.token = Output.concat(tokenID.apply(lambda x: f"{x}"), "=", tokenSecret.apply(lambda x: f"{x}"))
        return self
    
    def set_basic_auth(self, username: Input[str], password: Input[str]):
        self.username = username
        self.password = password
        return self
    
    def set_name(self, name: Input[str]):
        self.name = name 
        return self   
    
    def set_insecure(self, insecure: Input[bool]):
        self.insecure = insecure
        return self
    
    def build(self):
        if not self.token:
            return provider.Provider( 
                self.name,
                endpoint=self.url,
                username=self.username,
                password=self.password,
                insecure=self.insecure,
            )
        return provider.Provider( 
            self.name,
            endpoint=self.url,
            api_token=self.token,
            insecure=self.insecure,
        )