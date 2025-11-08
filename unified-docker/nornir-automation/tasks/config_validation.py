#!/usr/bin/env python3
"""
Configuration Validation Module
Handles NAPALM-based configuration validation and drift detection
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure
from nornir_utils.plugins.tasks.files import write_file
from nornir_utils.plugins.functions import print_result

logger = structlog.get_logger()

class ConfigValidator:
    """Handles configuration validation using NAPALM"""
    
    def __init__(self, config_dir: str = "/app/configs", inventory_dir: str = "/app/inventory"):
        self.config_dir = Path(config_dir)
        self.inventory_dir = Path(inventory_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.inventory_dir.mkdir(exist_ok=True)
        
        # Initialize Nornir
        self.nr = self._init_nornir()
    
    def _init_nornir(self) -> InitNornir:
        """Initialize Nornir with inventory and configuration"""
        try:
            # Create default inventory if it doesn't exist
            self._create_default_inventory()
            
            nr = InitNornir(
                inventory={
                    "plugin": "SimpleInventory",
                    "options": {
                        "host_file": str(self.inventory_dir / "hosts.yaml"),
                        "group_file": str(self.inventory_dir / "groups.yaml"),
                        "defaults_file": str(self.inventory_dir / "defaults.yaml")
                    }
                },
                logging={"enabled": True, "level": "INFO"}
            )
            
            logger.info("Nornir initialized successfully")
            return nr
            
        except Exception as e:
            logger.error("Failed to initialize Nornir", error=str(e))
            raise
    
    def _create_default_inventory(self):
        """Create default inventory files if they don't exist"""
        
        # Default hosts file
        hosts_file = self.inventory_dir / "hosts.yaml"
        if not hosts_file.exists():
            default_hosts = {
                "rtr-01": {
                    "hostname": "192.168.1.1",
                    "groups": ["routers", "cisco"],
                    "data": {
                        "vendor": "cisco",
                        "device_type": "ios",
                        "username": "admin",
                        "password": "admin123"
                    }
                },
                "sw-01": {
                    "hostname": "192.168.1.2", 
                    "groups": ["switches", "cisco"],
                    "data": {
                        "vendor": "cisco",
                        "device_type": "ios",
                        "username": "admin",
                        "password": "admin123"
                    }
                }
            }
            with open(hosts_file, 'w') as f:
                yaml.dump(default_hosts, f, default_flow_style=False)
        
        # Default groups file
        groups_file = self.inventory_dir / "groups.yaml"
        if not groups_file.exists():
            default_groups = {
                "routers": {
                    "data": {
                        "device_type": "ios",
                        "vendor": "cisco"
                    }
                },
                "switches": {
                    "data": {
                        "device_type": "ios", 
                        "vendor": "cisco"
                    }
                },
                "cisco": {
                    "data": {
                        "vendor": "cisco",
                        "platform": "ios"
                    }
                }
            }
            with open(groups_file, 'w') as f:
                yaml.dump(default_groups, f, default_flow_style=False)
        
        # Default defaults file
        defaults_file = self.inventory_dir / "defaults.yaml"
        if not defaults_file.exists():
            default_defaults = {
                "username": "admin",
                "password": "admin123",
                "port": 22,
                "platform": "ios",
                "connection_options": {
                    "napalm": {
                        "extras": {
                            "optional_args": {
                                "secret": "admin123"
                            }
                        }
                    }
                }
            }
            with open(defaults_file, 'w') as f:
                yaml.dump(default_defaults, f, default_flow_style=False)
    
    def get_device_config(self, device_name: str) -> Dict[str, Any]:
        """Get current configuration from a device"""
        try:
            device = self.nr.inventory.hosts[device_name]
            
            # Get running config using NAPALM
            result = self.nr.filter(name=device_name).run(
                task=napalm_get,
                getters=["config"]
            )
            
            if result.failed:
                logger.error("Failed to get config from device", device=device_name, error=result[device_name].exception)
                return {}
            
            config_data = result[device_name].result["config"]
            return {
                "running": config_data.get("running", ""),
                "startup": config_data.get("startup", ""),
                "candidate": config_data.get("candidate", "")
            }
            
        except Exception as e:
            logger.error("Error getting device config", device=device_name, error=str(e))
            return {}
    
    def save_source_of_truth_config(self, device_name: str, config: str, config_type: str = "running") -> bool:
        """Save configuration as source of truth"""
        try:
            config_file = self.config_dir / f"{device_name}_{config_type}.txt"
            with open(config_file, 'w') as f:
                f.write(config)
            
            # Also save as JSON with metadata
            metadata = {
                "device": device_name,
                "config_type": config_type,
                "timestamp": datetime.now().isoformat(),
                "source": "manual"
            }
            
            metadata_file = self.config_dir / f"{device_name}_{config_type}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Source of truth config saved", device=device_name, config_type=config_type)
            return True
            
        except Exception as e:
            logger.error("Failed to save source of truth config", device=device_name, error=str(e))
            return False
    
    def load_source_of_truth_config(self, device_name: str, config_type: str = "running") -> Optional[str]:
        """Load source of truth configuration"""
        try:
            config_file = self.config_dir / f"{device_name}_{config_type}.txt"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return f.read()
            return None
            
        except Exception as e:
            logger.error("Failed to load source of truth config", device=device_name, error=str(e))
            return None
    
    def compare_configurations(self, device_name: str, config_type: str = "running") -> Dict[str, Any]:
        """Compare live configuration with source of truth"""
        try:
            # Get live config
            live_configs = self.get_device_config(device_name)
            live_config = live_configs.get(config_type, "")
            
            # Get source of truth config
            sot_config = self.load_source_of_truth_config(device_name, config_type)
            
            if not sot_config:
                return {
                    "device": device_name,
                    "status": "error",
                    "message": "No source of truth configuration found",
                    "drift_detected": False,
                    "issues": []
                }
            
            # Simple line-by-line comparison
            live_lines = set(live_config.strip().split('\n'))
            sot_lines = set(sot_config.strip().split('\n'))
            
            # Find differences
            missing_in_live = sot_lines - live_lines
            extra_in_live = live_lines - sot_lines
            
            drift_detected = len(missing_in_live) > 0 or len(extra_in_live) > 0
            
            issues = []
            if missing_in_live:
                issues.append(f"Missing {len(missing_in_live)} lines from source of truth")
            if extra_in_live:
                issues.append(f"Extra {len(extra_in_live)} lines not in source of truth")
            
            return {
                "device": device_name,
                "status": "success",
                "drift_detected": drift_detected,
                "issues": issues,
                "missing_lines": list(missing_in_live),
                "extra_lines": list(extra_in_live),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Configuration comparison failed", device=device_name, error=str(e))
            return {
                "device": device_name,
                "status": "error",
                "message": str(e),
                "drift_detected": False,
                "issues": [f"Comparison error: {str(e)}"]
            }
    
    def validate_configurations(self, device_group: str, config_type: str = "all", dry_run: bool = True) -> List[Dict[str, Any]]:
        """Validate configurations for a device group"""
        try:
            # Filter devices by group
            if device_group == "all":
                devices = self.nr.inventory.hosts
            else:
                devices = self.nr.filter(groups__contains=device_group).inventory.hosts
            
            results = []
            
            for device_name in devices:
                logger.info("Validating device", device=device_name, group=device_group)
                
                if config_type == "all":
                    config_types = ["running", "startup"]
                else:
                    config_types = [config_type]
                
                for cfg_type in config_types:
                    result = self.compare_configurations(device_name, cfg_type)
                    results.append(result)
            
            # Save validation results
            self._save_validation_results(results)
            
            return results
            
        except Exception as e:
            logger.error("Validation failed", error=str(e))
            return [{
                "device": "unknown",
                "status": "error",
                "message": str(e),
                "drift_detected": False,
                "issues": [f"Validation error: {str(e)}"]
            }]
    
    def _save_validation_results(self, results: List[Dict[str, Any]]):
        """Save validation results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.config_dir / f"validation_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("Validation results saved", file=str(results_file))
            
        except Exception as e:
            logger.error("Failed to save validation results", error=str(e))
    
    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get validation history"""
        try:
            results_files = list(self.config_dir.glob("validation_results_*.json"))
            history = []
            
            for file_path in sorted(results_files, reverse=True):
                with open(file_path, 'r') as f:
                    results = json.load(f)
                    history.append({
                        "timestamp": file_path.stem.replace("validation_results_", ""),
                        "results": results
                    })
            
            return history
            
        except Exception as e:
            logger.error("Failed to get validation history", error=str(e))
            return []

