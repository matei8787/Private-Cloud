from abc import ABC, abstractmethod
from typing import Union, List, Any

class ServerBuilderInterface(ABC):
    
    
    def _get_param(self, source: Any, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Universal helper: retrieves value from dict OR object.
        Inherited by ALL builders (Proxmox, AWS, GCP).
        """
        value = default
        
        # 1. Try Dictionary Access
        if isinstance(source, dict):
            if required and key not in source:
                raise ValueError(f"Missing required key '{key}' in configuration: {source}")
            value = source.get(key, default)
            
        # 2. Try Object Attribute Access
        else:
            # We treat 'source' as an object
            if required and not hasattr(source, key):
                raise ValueError(f"Missing required attribute '.{key}' in configuration object: {source}")
            value = getattr(source, key, default)
            
        return value
    
    @abstractmethod
    def set_name(self, name):
        pass
    
    @abstractmethod
    def set_resources(self, cpu, memory, storage, network_adapters):
        pass
    
    @abstractmethod
    def set_static_network(self, cidr):
        pass
    
    @abstractmethod
    def set_initialization(self):
        pass
    
    @abstractmethod
    def set_opts(self, provider=None, **kwargs):
        pass
    
    @abstractmethod
    def build(self):
        pass