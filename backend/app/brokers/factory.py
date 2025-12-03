"""Factory pattern for instantiating broker adapters"""

from typing import Dict, Any
from .base import IBrokerAdapter
from .mock_broker import MockBrokerAdapter


class BrokerFactory:
    """Factory for creating broker adapter instances"""
    
    _adapters: Dict[str, type] = {
        "mock": MockBrokerAdapter,
    }
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: type) -> None:
        """
        Register a new broker adapter
        
        Args:
            name: Name identifier for the broker
            adapter_class: Class implementing IBrokerAdapter
        """
        cls._adapters[name] = adapter_class
    
    @classmethod
    def create(cls, broker_name: str, credentials: Dict[str, Any] = None) -> IBrokerAdapter:
        """
        Create a broker adapter instance
        
        Args:
            broker_name: Name of the broker ('mock', 'ibkr', 'zerodha', 'alpaca')
            credentials: Optional credentials dictionary
            
        Returns:
            Instance of the broker adapter
            
        Raises:
            ValueError: If broker name is not recognized
        """
        if broker_name not in cls._adapters:
            raise ValueError(
                f"Unknown broker: {broker_name}. "
                f"Available brokers: {', '.join(cls._adapters.keys())}"
            )
        
        adapter_class = cls._adapters[broker_name]
        return adapter_class()
    
    @classmethod
    def list_available_brokers(cls) -> list[str]:
        """Get list of available broker adapters"""
        return list(cls._adapters.keys())
