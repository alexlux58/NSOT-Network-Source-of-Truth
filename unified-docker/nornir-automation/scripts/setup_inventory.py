#!/usr/bin/env python3
"""
Setup Inventory Script
Creates initial inventory files and syncs with NetBox/Nautobot
"""

import os
import sys
import argparse
import yaml
import json
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append('/app')

from tasks.inventory_manager import InventoryManager

def create_sample_inventory():
    """Create sample inventory files for testing"""
    
    # Sample hosts
    hosts = {
        "rtr-01": {
            "hostname": "192.168.1.1",
            "groups": ["routers", "cisco"],
            "data": {
                "vendor": "cisco",
                "device_type": "ios",
                "username": "admin",
                "password": "admin123",
                "site": "datacenter-1",
                "status": "active"
            }
        },
        "rtr-02": {
            "hostname": "192.168.1.2", 
            "groups": ["routers", "cisco"],
            "data": {
                "vendor": "cisco",
                "device_type": "ios",
                "username": "admin",
                "password": "admin123",
                "site": "datacenter-1",
                "status": "active"
            }
        },
        "sw-01": {
            "hostname": "192.168.1.10",
            "groups": ["switches", "cisco"],
            "data": {
                "vendor": "cisco",
                "device_type": "ios",
                "username": "admin",
                "password": "admin123",
                "site": "datacenter-1",
                "status": "active"
            }
        },
        "sw-02": {
            "hostname": "192.168.1.11",
            "groups": ["switches", "cisco"],
            "data": {
                "vendor": "cisco",
                "device_type": "ios",
                "username": "admin",
                "password": "admin123",
                "site": "datacenter-1",
                "status": "active"
            }
        },
        "fw-01": {
            "hostname": "192.168.1.20",
            "groups": ["firewalls", "fortinet"],
            "data": {
                "vendor": "fortinet",
                "device_type": "fortios",
                "username": "admin",
                "password": "admin123",
                "site": "datacenter-1",
                "status": "active"
            }
        }
    }
    
    # Sample groups
    groups = {
        "routers": {
            "data": {
                "device_type": "ios",
                "vendor": "cisco",
                "description": "Core and edge routers"
            }
        },
        "switches": {
            "data": {
                "device_type": "ios",
                "vendor": "cisco", 
                "description": "Access and distribution switches"
            }
        },
        "firewalls": {
            "data": {
                "device_type": "fortios",
                "vendor": "fortinet",
                "description": "Security appliances"
            }
        },
        "cisco": {
            "data": {
                "vendor": "cisco",
                "platform": "ios",
                "description": "Cisco devices"
            }
        },
        "fortinet": {
            "data": {
                "vendor": "fortinet",
                "platform": "fortios",
                "description": "Fortinet devices"
            }
        }
    }
    
    # Sample defaults
    defaults = {
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
    
    # Write files
    inventory_dir = Path("/app/inventory")
    inventory_dir.mkdir(exist_ok=True)
    
    with open(inventory_dir / "hosts.yaml", 'w') as f:
        yaml.dump(hosts, f, default_flow_style=False, sort_keys=False)
    
    with open(inventory_dir / "groups.yaml", 'w') as f:
        yaml.dump(groups, f, default_flow_style=False, sort_keys=False)
    
    with open(inventory_dir / "defaults.yaml", 'w') as f:
        yaml.dump(defaults, f, default_flow_style=False, sort_keys=False)
    
    print("Sample inventory created successfully!")
    print(f"Created {len(hosts)} hosts, {len(groups)} groups")

def sync_from_netbox(api_token):
    """Sync inventory from NetBox"""
    try:
        inventory_manager = InventoryManager()
        success = inventory_manager.sync_from_netbox(api_token)
        
        if success:
            print("Successfully synced inventory from NetBox")
        else:
            print("Failed to sync inventory from NetBox")
            
    except Exception as e:
        print(f"Error syncing from NetBox: {e}")

def sync_from_nautobot(api_token):
    """Sync inventory from Nautobot"""
    try:
        inventory_manager = InventoryManager()
        success = inventory_manager.sync_from_nautobot(api_token)
        
        if success:
            print("Successfully synced inventory from Nautobot")
        else:
            print("Failed to sync inventory from Nautobot")
            
    except Exception as e:
        print(f"Error syncing from Nautobot: {e}")

def main():
    parser = argparse.ArgumentParser(description="Setup Nornir inventory")
    parser.add_argument("--sample", action="store_true", help="Create sample inventory")
    parser.add_argument("--netbox", help="Sync from NetBox (provide API token)")
    parser.add_argument("--nautobot", help="Sync from Nautobot (provide API token)")
    
    args = parser.parse_args()
    
    if args.sample:
        create_sample_inventory()
    
    if args.netbox:
        sync_from_netbox(args.netbox)
    
    if args.nautobot:
        sync_from_nautobot(args.nautobot)
    
    if not any([args.sample, args.netbox, args.nautobot]):
        print("No action specified. Use --help for options.")
        print("Example: python setup_inventory.py --sample")

if __name__ == "__main__":
    main()

