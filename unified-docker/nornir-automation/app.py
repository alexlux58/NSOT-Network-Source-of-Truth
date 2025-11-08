#!/usr/bin/env python3
"""
Nornir Automation Web Application
Provides web interface for network configuration validation and automation
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from werkzeug.exceptions import BadRequest
import structlog

from tasks.config_validation import ConfigValidator
from tasks.inventory_manager import InventoryManager
from tasks.report_generator import ReportGenerator
from web.routes import main_bp, api_bp

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(app)
    
    # Initialize API
    api = Api(
        app,
        version='1.0',
        title='Nornir Automation API',
        description='Network configuration validation and automation API',
        doc='/api/docs/'
    )
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Initialize services
    app.config_validator = ConfigValidator()
    app.inventory_manager = InventoryManager()
    app.report_generator = ReportGenerator()
    
    # API Models
    validation_request = api.model('ValidationRequest', {
        'device_group': fields.String(required=True, description='Device group to validate'),
        'config_type': fields.String(required=False, description='Configuration type to validate'),
        'dry_run': fields.Boolean(required=False, description='Perform dry run without changes')
    })
    
    validation_result = api.model('ValidationResult', {
        'device': fields.String(description='Device name'),
        'status': fields.String(description='Validation status'),
        'drift_detected': fields.Boolean(description='Configuration drift detected'),
        'issues': fields.List(fields.String, description='List of issues found'),
        'timestamp': fields.DateTime(description='Validation timestamp')
    })
    
    # API Routes
    @api.route('/health')
    class Health(Resource):
        def get(self):
            """Health check endpoint"""
            return {'status': 'healthy', 'service': 'nornir-automation'}
    
    @api.route('/inventory')
    class Inventory(Resource):
        def get(self):
            """Get device inventory"""
            try:
                inventory = app.inventory_manager.get_inventory()
                return {'inventory': inventory}
            except Exception as e:
                logger.error("Failed to get inventory", error=str(e))
                return {'error': str(e)}, 500
    
    @api.route('/validate')
    class Validate(Resource):
        @api.expect(validation_request)
        @api.marshal_with(validation_result)
        def post(self):
            """Validate device configurations"""
            try:
                data = request.get_json()
                device_group = data.get('device_group')
                config_type = data.get('config_type', 'all')
                dry_run = data.get('dry_run', True)
                
                results = app.config_validator.validate_configurations(
                    device_group=device_group,
                    config_type=config_type,
                    dry_run=dry_run
                )
                
                return results
            except Exception as e:
                logger.error("Validation failed", error=str(e))
                return {'error': str(e)}, 500
    
    @api.route('/reports')
    class Reports(Resource):
        def get(self):
            """Get available reports"""
            try:
                reports = app.report_generator.list_reports()
                return {'reports': reports}
            except Exception as e:
                logger.error("Failed to list reports", error=str(e))
                return {'error': str(e)}, 500
    
    @api.route('/reports/<report_id>')
    class Report(Resource):
        def get(self, report_id):
            """Get specific report"""
            try:
                report = app.report_generator.get_report(report_id)
                return report
            except Exception as e:
                logger.error("Failed to get report", error=str(e), report_id=report_id)
                return {'error': str(e)}, 500
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Nornir Automation service")
    app.run(host='0.0.0.0', port=8082, debug=True)

