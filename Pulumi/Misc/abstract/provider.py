from abc import ABC, abstractmethod

class ProviderBuilderInterface(ABC):
    
    @abstractmethod
    def set_url(self, url):
        pass
    
    @abstractmethod
    def set_token(self, tokenID, tokenSecret):
        pass
    
    @abstractmethod
    def set_basic_auth(self, username, password):
        pass
    
    @abstractmethod
    def build(self):
        pass