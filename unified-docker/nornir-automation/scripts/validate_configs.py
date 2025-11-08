#!/usr/bin/env python3
"""
Configuration Validation Script
Command-line interface for running configuration validation
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append('/app')

from tasks.config_validation import ConfigValidator
from tasks.report_generator import ReportGenerator

def run_validation(device_group, config_type, dry_run, output_format):
    """Run configuration validation"""
    try:
        validator = ConfigValidator()
        results = validator.validate_configurations(
            device_group=device_group,
            config_type=config_type,
            dry_run=dry_run
        )
        
        # Generate report
        if output_format != "json":
            report_generator = ReportGenerator()
            report_file = report_generator.generate_validation_report(
                results, output_format
            )
            print(f"Report generated: {report_file}")
        else:
            # Print JSON results to stdout
            print(json.dumps(results, indent=2))
        
        # Print summary
        total_devices = len(results)
        devices_with_drift = len([r for r in results if r.get("drift_detected", False)])
        devices_with_errors = len([r for r in results if r.get("status") == "error"])
        
        print(f"\nValidation Summary:")
        print(f"Total devices: {total_devices}")
        print(f"Devices with drift: {devices_with_drift}")
        print(f"Devices with errors: {devices_with_errors}")
        
        return results
        
    except Exception as e:
        print(f"Validation failed: {e}")
        return []

def save_source_of_truth(device_name, config_type):
    """Save current configuration as source of truth"""
    try:
        validator = ConfigValidator()
        configs = validator.get_device_config(device_name)
        config = configs.get(config_type, "")
        
        if not config:
            print(f"No {config_type} configuration found for {device_name}")
            return False
        
        success = validator.save_source_of_truth_config(device_name, config, config_type)
        
        if success:
            print(f"Source of truth saved for {device_name} ({config_type})")
        else:
            print(f"Failed to save source of truth for {device_name}")
        
        return success
        
    except Exception as e:
        print(f"Error saving source of truth: {e}")
        return False

def compare_configs(device_name, config_type):
    """Compare live configuration with source of truth"""
    try:
        validator = ConfigValidator()
        result = validator.compare_configurations(device_name, config_type)
        
        print(f"Configuration comparison for {device_name} ({config_type}):")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Drift detected: {result.get('drift_detected', False)}")
        
        if result.get('issues'):
            print("Issues found:")
            for issue in result['issues']:
                print(f"  - {issue}")
        
        if result.get('missing_lines'):
            print(f"Missing lines ({len(result['missing_lines'])}):")
            for line in result['missing_lines'][:10]:  # Show first 10
                print(f"  - {line}")
            if len(result['missing_lines']) > 10:
                print(f"  ... and {len(result['missing_lines']) - 10} more")
        
        if result.get('extra_lines'):
            print(f"Extra lines ({len(result['extra_lines'])}):")
            for line in result['extra_lines'][:10]:  # Show first 10
                print(f"  - {line}")
            if len(result['extra_lines']) > 10:
                print(f"  ... and {len(result['extra_lines']) - 10} more")
        
        return result
        
    except Exception as e:
        print(f"Error comparing configurations: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Configuration validation tool")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validation command
    validate_parser = subparsers.add_parser('validate', help='Run configuration validation')
    validate_parser.add_argument('--device-group', default='all', help='Device group to validate')
    validate_parser.add_argument('--config-type', default='running', help='Configuration type to validate')
    validate_parser.add_argument('--dry-run', action='store_true', default=True, help='Perform dry run')
    validate_parser.add_argument('--live', action='store_true', help='Perform live validation (not dry run)')
    validate_parser.add_argument('--format', choices=['json', 'csv', 'xlsx', 'html'], default='json', help='Output format')
    
    # Save source of truth command
    save_parser = subparsers.add_parser('save-sot', help='Save current config as source of truth')
    save_parser.add_argument('device_name', help='Device name')
    save_parser.add_argument('--config-type', default='running', help='Configuration type')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare live config with source of truth')
    compare_parser.add_argument('device_name', help='Device name')
    compare_parser.add_argument('--config-type', default='running', help='Configuration type')
    
    args = parser.parse_args()
    
    if args.command == 'validate':
        dry_run = args.dry_run and not args.live
        run_validation(
            device_group=args.device_group,
            config_type=args.config_type,
            dry_run=dry_run,
            output_format=args.format
        )
    
    elif args.command == 'save-sot':
        save_source_of_truth(args.device_name, args.config_type)
    
    elif args.command == 'compare':
        compare_configs(args.device_name, args.config_type)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

