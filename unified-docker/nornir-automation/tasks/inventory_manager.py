#!/usr/bin/env python3
"""
Inventory Management Module
Handles device inventory management and integration with NetBox/Nautobot
"""

import os
import json
import yaml
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()

class InventoryManager:
    """Manages device inventory and integrates with NetBox/Nautobot"""
    
    def __init__(self, 
                 inventory_dir: str = "/app/inventory",
                 netbox_url: str = "http://netbox:8080",
                 nautobot_url: str = "http://nautobot:8080"):
        self.inventory_dir = Path(inventory_dir)
        self.netbox_url = netbox_url
        self.nautobot_url = nautobot_url
        self.inventory_dir.mkdir(exist_ok=True)
    
    def get_inventory(self) -> Dict[str, Any]:
        """Get current device inventory"""
        try:
            # Load from local inventory files
            hosts_file = self.inventory_dir / "hosts.yaml"
            groups_file = self.inventory_dir / "groups.yaml"
            defaults_file = self.inventory_dir / "defaults.yaml"
            
            inventory = {
                "hosts": {},
                "groups": {},
                "defaults": {}
            }
            
            if hosts_file.exists():
                with open(hosts_file, 'r') as f:
                    inventory["hosts"] = yaml.safe_load(f) or {}
            
            if groups_file.exists():
                with open(groups_file, 'r') as f:
                    inventory["groups"] = yaml.safe_load(f) or {}
            
            if defaults_file.exists():
                with open(defaults_file, 'r') as f:
                    inventory["defaults"] = yaml.safe_load(f) or {}
            
            return inventory
            
        except Exception as e:
            logger.error("Failed to get inventory", error=str(e))
            return {"hosts": {}, "groups": {}, "defaults": {}}
    
    def sync_from_netbox(self, api_token: str) -> bool:
        """Sync inventory from NetBox"""
        try:
            headers = {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json"
            }
            
            # Get devices from NetBox
            devices_url = f"{self.netbox_url}/api/dcim/devices/"
            response = requests.get(devices_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            devices_data = response.json()
            devices = devices_data.get("results", [])
            
            # Convert NetBox devices to Nornir inventory format
            hosts = {}
            for device in devices:
                device_name = device.get("name", "")
                if not device_name:
                    continue
                
                # Extract device information
                primary_ip = device.get("primary_ip", {})
                ip_address = ""
                if primary_ip and "address" in primary_ip:
                    ip_address = primary_ip["address"].split("/")[0]  # Remove CIDR notation
                
                # Get device type and manufacturer
                device_type = device.get("device_type", {})
                manufacturer = device_type.get("manufacturer", {}).get("name", "").lower()
                
                # Map manufacturer to NAPALM driver
                napalm_driver = self._map_manufacturer_to_driver(manufacturer)
                
                # Get device role for grouping
                device_role = device.get("device_role", {}).get("name", "").lower()
                
                hosts[device_name] = {
                    "hostname": ip_address or device.get("display", ""),
                    "groups": [device_role, manufacturer] if device_role and manufacturer else [],
                    "data": {
                        "vendor": manufacturer,
                        "device_type": napalm_driver,
                        "site": device.get("site", {}).get("name", ""),
                        "status": device.get("status", {}).get("value", ""),
                        "serial": device.get("serial", ""),
                        "asset_tag": device.get("asset_tag", ""),
                        "netbox_id": device.get("id", ""),
                        "netbox_url": device.get("url", "")
                    }
                }
            
            # Save updated inventory
            self._save_hosts_inventory(hosts)
            
            logger.info("Inventory synced from NetBox", device_count=len(hosts))
            return True
            
        except Exception as e:
            logger.error("Failed to sync from NetBox", error=str(e))
            return False
    
    def sync_from_nautobot(self, api_token: str) -> bool:
        """Sync inventory from Nautobot"""
        try:
            headers = {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json"
            }
            
            # Get devices from Nautobot
            devices_url = f"{self.nautobot_url}/api/dcim/devices/"
            response = requests.get(devices_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            devices_data = response.json()
            devices = devices_data.get("results", [])
            
            # Convert Nautobot devices to Nornir inventory format
            hosts = {}
            for device in devices:
                device_name = device.get("name", "")
                if not device_name:
                    continue
                
                # Extract device information
                primary_ip = device.get("primary_ip4", {})
                ip_address = ""
                if primary_ip and "address" in primary_ip:
                    ip_address = primary_ip["address"].split("/")[0]  # Remove CIDR notation
                
                # Get device type and manufacturer
                device_type = device.get("device_type", {})
                manufacturer = device_type.get("manufacturer", {}).get("name", "").lower()
                
                # Map manufacturer to NAPALM driver
                napalm_driver = self._map_manufacturer_to_driver(manufacturer)
                
                # Get device role for grouping
                device_role = device.get("device_role", {}).get("name", "").lower()
                
                hosts[device_name] = {
                    "hostname": ip_address or device.get("display", ""),
                    "groups": [device_role, manufacturer] if device_role and manufacturer else [],
                    "data": {
                        "vendor": manufacturer,
                        "device_type": napalm_driver,
                        "site": device.get("site", {}).get("name", ""),
                        "status": device.get("status", {}).get("value", ""),
                        "serial": device.get("serial", ""),
                        "asset_tag": device.get("asset_tag", ""),
                        "nautobot_id": device.get("id", ""),
                        "nautobot_url": device.get("url", "")
                    }
                }
            
            # Save updated inventory
            self._save_hosts_inventory(hosts)
            
            logger.info("Inventory synced from Nautobot", device_count=len(hosts))
            return True
            
        except Exception as e:
            logger.error("Failed to sync from Nautobot", error=str(e))
            return False
    
    def _map_manufacturer_to_driver(self, manufacturer: str) -> str:
        """Map manufacturer name to NAPALM driver"""
        mapping = {
            "cisco": "ios",
            "juniper": "junos",
            "arista": "eos",
            "hp": "procurve",
            "huawei": "vrp",
            "fortinet": "fortios",
            "palo alto": "panos",
            "mikrotik": "ros",
            "f5": "f5",
            "nxos": "nxos",
            "iosxr": "iosxr"
        }
        
        manufacturer_lower = manufacturer.lower()
        for key, driver in mapping.items():
            if key in manufacturer_lower:
                return driver
        
        return "ios"  # Default fallback
    
    def _save_hosts_inventory(self, hosts: Dict[str, Any]):
        """Save hosts inventory to file"""
        try:
            hosts_file = self.inventory_dir / "hosts.yaml"
            with open(hosts_file, 'w') as f:
                yaml.dump(hosts, f, default_flow_style=False, sort_keys=False)
            
            logger.info("Hosts inventory saved", file=str(hosts_file))
            
        except Exception as e:
            logger.error("Failed to save hosts inventory", error=str(e))
    
    def add_device(self, device_name: str, hostname: str, groups: List[str], 
                   vendor: str, device_type: str, **kwargs) -> bool:
        """Add a new device to inventory"""
        try:
            # Load current inventory
            inventory = self.get_inventory()
            hosts = inventory.get("hosts", {})
            
            # Add new device
            hosts[device_name] = {
                "hostname": hostname,
                "groups": groups,
                "data": {
                    "vendor": vendor,
                    "device_type": device_type,
                    **kwargs
                }
            }
            
            # Save updated inventory
            self._save_hosts_inventory(hosts)
            
            logger.info("Device added to inventory", device=device_name)
            return True
            
        except Exception as e:
            logger.error("Failed to add device", device=device_name, error=str(e))
            return False
    
    def remove_device(self, device_name: str) -> bool:
        """Remove device from inventory"""
        try:
            # Load current inventory
            inventory = self.get_inventory()
            hosts = inventory.get("hosts", {})
            
            if device_name in hosts:
                del hosts[device_name]
                self._save_hosts_inventory(hosts)
                logger.info("Device removed from inventory", device=device_name)
                return True
            else:
                logger.warning("Device not found in inventory", device=device_name)
                return False
                
        except Exception as e:
            logger.error("Failed to remove device", device=device_name, error=str(e))
            return False
    
    def get_device_groups(self) -> List[str]:
        """Get list of device groups"""
        try:
            inventory = self.get_inventory()
            groups = set()
            
            for host_data in inventory.get("hosts", {}).values():
                host_groups = host_data.get("groups", [])
                groups.update(host_groups)
            
            return sorted(list(groups))
            
        except Exception as e:
            logger.error("Failed to get device groups", error=str(e))
            return []
    
    def get_devices_by_group(self, group_name: str) -> List[str]:
        """Get devices in a specific group"""
        try:
            inventory = self.get_inventory()
            devices = []
            
            for device_name, host_data in inventory.get("hosts", {}).items():
                if group_name in host_data.get("groups", []):
                    devices.append(device_name)
            
            return devices
            
        except Exception as e:
            logger.error("Failed to get devices by group", group=group_name, error=str(e))
            return []

