"""
Main API logic goes here
"""
import ipaddress
import logging
import os
import socket
import time

from datetime import datetime
from flasgger import Swagger
from flask import request, jsonify, Blueprint
from prometheus_client import generate_latest, Counter, Histogram
from src import app, db
from src.models.domain_lookup import DomainLookup

API_VERSION = "0.1.0"

swagger_config = {
    "swagger": "2.0",
    "info": {
        "title": "Project Baobab API",
        "description": "This is an API to discover domains.",
        "version": API_VERSION,
    },
    "basePath": "/",
    "definitions": {
        "handlers.HealthStatus": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string"
                }
            }
        },
        "handlers.Status": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "integer"
                },
                "kubernetes": {
                    "type": "boolean"
                },
                "version": {
                    "type": "string"
                }
            }
        },
        "handlers.ValidateIPRequest": {
            "type": "object",
            "properties": {
                "ip": {
                    "type": "string"
                }
            }
        },
        "handlers.ValidateIPResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "boolean"
                }
            }
        },
        "models.Address": {
            "type": "object",
            "properties": {
                "ip": {
                    "type": "string"
                },
                "queryID": {
                    "type": "integer"
                }
            }
        },
        "models.Query": {
            "type": "object",
            "properties": {
                "addresses": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/models.Address"
                    }
                },
                "client_ip": {
                    "type": "string"
                },
                "created_time": {
                    "type": "integer"
                },
                "domain": {
                    "type": "string"
                },
                "queryID": {
                    "type": "integer"
                }
            }
        },
        "utils.HTTPError": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string"
                }
            }
        }
    }
}

swagger = Swagger(app, template=swagger_config)

domain_lookup = Blueprint("domain_lookup", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('access')

@domain_lookup.before_request
def log_request_info():
    """
    Log basic client info before requests
    """
    logger.info('[%s] %s - IP: {request.remote_addr}', request.method, request.url)
    logger.info('Headers: %s', request.headers)
    if request.method in ['POST', 'PUT', 'PATCH']:
        logger.info('Body: %s', request.get_data())


@domain_lookup.route('/', methods=['GET'])
def query_status():
    """
    Show current status
    ---
    tags:
      - status
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/handlers.Status'
    """
    current_time = int(time.time())

    kubernetes = os.getenv('KUBERNETES_SERVICE_HOST') is not None

    response = {
        "version": API_VERSION,
        "date": current_time,
        "kubernetes": kubernetes
    }

    return jsonify(response)

@domain_lookup.route('/health', methods=['GET'])
def query_health():
    """
    Show health status
    ---
    tags:
      - health
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/handlers.HealthStatus'
    """
    return jsonify({"status": "healthy"})

@domain_lookup.route('/v1/history', methods=['GET'])
def queries_history():
    """
    List queries
    ---
    tags:
      - history
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/models.Query'
      400:
        description: Bad Request
        schema:
          $ref: '#/definitions/utils.HTTPError'
    """
    history = DomainLookup.query.order_by(DomainLookup.lookup_date.desc()).limit(20).all()

    if not history:
        return jsonify({"message": "No history found"}), 400

    response = []
    response = [entry.to_dict() for entry in history]

    return jsonify(response)

@domain_lookup.route('/v1/tools/lookup', methods=['GET'])
def lookup_domain():
    """
    Lookup domain and return all IPv4 addresses
    ---
    tags:
      - tools
    parameters:
      - "type": "string"
        "description": "Domain name"
        "name": "domain"
        "in": "query"
        "required": true

    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/models.Query'
      400:
        description: Bad Request
        schema:
          $ref: '#/definitions/utils.HTTPError'
      404:
        description: Not Found
        schema:
          $ref: '#/definitions/utils.HTTPError'
    """
    domain = request.args.get('domain')

    if not domain:
        return jsonify({"message": "Domain parameter is required"}), 400

    try:
        # Resolve IPv4 addresses
        ipv4_addresses = [ip[4][0] for ip in socket.getaddrinfo(domain, None, socket.AF_INET)]

        # Check if a record for this domain already exists
        existing_record = DomainLookup.query.filter_by(domain=domain).first()

        if existing_record:
            # Update existing record with new IP addresses
            existing_record.ipv4_addresses = str(ipv4_addresses)
            existing_record.lookup_date = datetime.utcnow()
        else:
            # Create a new record
            lookup_entry = DomainLookup(domain=domain, ipv4_addresses=str(ipv4_addresses))
            db.session.add(lookup_entry)

        db.session.commit()
        response = DomainLookup.query.filter_by(domain=domain).first()

        return jsonify(response.to_dict())
    except socket.gaierror:
        return jsonify({"message": "Invalid domain or unable to resolve domain"}), 404


@domain_lookup.route('/v1/tools/validate', methods=['POST'])
def validate_ipv4():
    """
    Simple IP validation
    ---
    tags:
      - tools
    parameters:
      - name: request
        in: body
        required: true
        schema:
          $ref: '#/definitions/handlers.ValidateIPRequest'
    responses:
      200:
        description: OK
        schema:
          $ref: '#/definitions/handlers.ValidateIPResponse'
      400:
        description: Bad Request
        schema:
          $ref: '#/definitions/utils.HTTPError'
    """
    data = request.json
    if not data or 'ip' not in data:
        return jsonify({"message": "IP parameter is required"}), 400

    ip = data['ip']

    try:
        # Validate if the input is a valid IPv4 address
        ip_obj = ipaddress.ip_address(ip)
        is_valid = isinstance(ip_obj, ipaddress.IPv4Address)
    except ValueError:
        is_valid = False

    response = {
        "status": is_valid
    }

    return jsonify(response), 200

# Define Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'API request latency')

@domain_lookup.before_request
@REQUEST_LATENCY.time()
def before_request():
    """
    Increment the request count for each incoming request
    """

    REQUEST_COUNT.inc()

@domain_lookup.route('/metrics')
def metrics():
    """
    Generate and return metrics in Prometheus format
    """
    return generate_latest()
