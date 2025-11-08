#!/usr/bin/env python3
"""
Web Routes Module
Defines web interface routes for the Nornir automation application
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import structlog

logger = structlog.get_logger()

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

@main_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@main_bp.route('/inventory')
def inventory():
    """Inventory management page"""
    return render_template('inventory.html')

@main_bp.route('/validation')
def validation():
    """Configuration validation page"""
    return render_template('validation.html')

@main_bp.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

@main_bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@api_bp.route('/devices')
def get_devices():
    """API endpoint to get devices"""
    try:
        # This would typically get data from the inventory manager
        # For now, return mock data
        devices = [
            {
                "name": "rtr-01",
                "hostname": "192.168.1.1",
                "vendor": "cisco",
                "device_type": "ios",
                "status": "active",
                "groups": ["routers", "cisco"]
            },
            {
                "name": "sw-01", 
                "hostname": "192.168.1.2",
                "vendor": "cisco",
                "device_type": "ios",
                "status": "active",
                "groups": ["switches", "cisco"]
            }
        ]
        return jsonify({"devices": devices})
    except Exception as e:
        logger.error("Failed to get devices", error=str(e))
        return jsonify({"error": str(e)}), 500

@api_bp.route('/validation/run', methods=['POST'])
def run_validation():
    """API endpoint to run configuration validation"""
    try:
        data = request.get_json()
        device_group = data.get('device_group', 'all')
        config_type = data.get('config_type', 'running')
        dry_run = data.get('dry_run', True)
        
        # This would typically call the config validator
        # For now, return mock results
        results = [
            {
                "device": "rtr-01",
                "status": "success",
                "drift_detected": False,
                "issues": [],
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "device": "sw-01",
                "status": "success", 
                "drift_detected": True,
                "issues": ["Missing VLAN configuration", "Extra interface description"],
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
        
        return jsonify({"results": results})
    except Exception as e:
        logger.error("Validation failed", error=str(e))
        return jsonify({"error": str(e)}), 500

@api_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """API endpoint to generate reports"""
    try:
        data = request.get_json()
        report_format = data.get('format', 'json')
        validation_results = data.get('results', [])
        
        # This would typically call the report generator
        # For now, return mock response
        report_id = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            "report_id": report_id,
            "format": report_format,
            "status": "generated"
        })
    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        return jsonify({"error": str(e)}), 500

