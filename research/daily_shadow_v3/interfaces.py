"""Provider-neutral collection contract; implementations must return explicit basis/availability."""
from typing import Protocol
from .adapter import Snapshot
from .legal import Permit
class Transport(Protocol):
    fixture:bool
    def get(self,path:str,query:dict,secret:str)->bytes:...
class EODProvider(Protocol):
    permit:Permit
    transport:Transport
    def collect(self,session:str)->Snapshot:...
