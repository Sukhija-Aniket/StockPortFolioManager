"""
Participant Configuration Manager for Worker
Handles participant-specific calculation rates and configurations
"""

import json
import os
from typing import Dict, Any
from worker.config.logging_config import setup_logging

logger = setup_logging(__name__)

class ParticipantConfigManager:
    """Manages participant-specific calculation configurations"""
    
    def __init__(self):
        """
        Initialize the participant config manager
        
        Args:
            config_file_path: Path to the JSON config file. If None, uses default path.
        """
        current_dir = os.path.dirname(__file__)
        self.config_file_path = os.path.join(current_dir, 'participant_rates.json')
        
        self.participant_configs = self._load_config()
        
    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """Load participant configurations from JSON file"""
        try:
            if not os.path.exists(self.config_file_path):
                raise FileNotFoundError(f"Config file not found at {self.config_file_path}")
            
            with open(self.config_file_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded participant config with {len(config)} participants")
            return config
            
        except Exception as e:
            logger.error(f"Error loading participant config: {e}")
            raise
    
    
    def get_participant_config(self, participant_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific participant
        
        Args:
            participant_name: Name of the participant (case-insensitive)
            
        Returns:
            Dict containing participant configuration
            
        Raises:
            ValueError: If participant not found in config
        """
        try:
            # Normalize participant name
            participant_key = participant_name.lower()
            
            if participant_key in self.participant_configs:
                return self.participant_configs[participant_key]
            else:
                raise ValueError(f"Participant '{participant_name}' not found in config")
                
        except Exception as e:
            logger.error(f"Error getting participant config for '{participant_name}': {e}")
            raise
    
    def get_stt_rate(self, participant_name: str, is_intraday: bool = False) -> float:
        """Get STT rate for a participant"""
        config = self.get_participant_config(participant_name)
        stt_rates = config["stt_rates"]
        
        if is_intraday:
            return stt_rates["intraday"]
        else:
            return stt_rates["delivery"]
    
    def get_brokerage_rate(self, participant_name: str) -> Dict[str, Any]:
        """Get brokerage configuration for a participant"""
        config = self.get_participant_config(participant_name)
        return config["brokerage"]
    
    def get_transaction_charges_rate(self, participant_name: str) -> float:
        """Get transaction charges rate for a participant"""
        config = self.get_participant_config(participant_name)
        return config["transaction_charges"]
    
    def get_stamp_duty_rate(self, participant_name: str) -> float:
        """Get stamp duty rate for a participant"""
        config = self.get_participant_config(participant_name)
        return config["stamp_duty"]
    
    def get_dp_charges(self, participant_name: str) -> float:
        """Get DP charges for a participant"""
        config = self.get_participant_config(participant_name)
        return config["dp_charges"]
    
    def get_gst_rate(self, participant_name: str) -> float:
        """Get GST rate for a participant"""
        config = self.get_participant_config(participant_name)
        return config["gst_rate"]
    
    def get_exchange_transaction_charges_rate(self, participant_name: str) -> float:
        """Get exchange transaction charges rate for a participant"""
        config = self.get_participant_config(participant_name)
        return config["exchange_transaction_charges"]
    
    def reload_config(self):
        """Reload configuration from file"""
        self.participant_configs = self._load_config()
        logger.info("Participant config reloaded")
    
    def list_participants(self) -> list:
        """Get list of all configured participants"""
        return list(self.participant_configs.keys())
    
    def add_participant(self, participant_name: str, config: Dict[str, Any]):
        """Add or update a participant configuration"""
        try:
            participant_key = participant_name.value.lower()
            self.participant_configs[participant_key] = config
            
            # Save to file
            with open(self.config_file_path, 'w') as f:
                json.dump(self.participant_configs, f, indent=2)
            
            logger.info(f"Added/updated participant: {participant_name}")
            
        except Exception as e:
            logger.error(f"Error adding participant '{participant_name}': {e}")
            raise 