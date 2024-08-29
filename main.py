from datetime import datetime
from flasgger import Swagger
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST
import ipaddress
import logging
import os
import socket
# import signal
# import sys
import time

app = Flask(__name__)
swagger = Swagger(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('access')

@app.before_request
def log_request_info():
    logger.info(f'[{request.method}] {request.url} - IP: {request.remote_addr}')
    logger.info(f'Headers: {request.headers}')
    if request.method in ['POST', 'PUT', 'PATCH']:
        logger.info(f'Body: {request.get_data()}')

# def handle_signal(sig, frame):
#     print(f'Received signal {sig}, shutting down gracefully...')
#     # Perform any cleanup here, like closing database connections
#     sys.exit(0)

# signal.signal(signal.SIGINT, handle_signal)
# signal.signal(signal.SIGTERM, handle_signal) 

# @app.route('/longtask')
# def long_task():
#     # Simulate a long task
#     time.sleep(10)
#     return "Task complete!"

@app.route('/', methods=['GET'])
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
          id: Status
          properties:
            date:
              type: integer
            kubernetes:
              type: boolean
            version:
              type: string
    """
    current_time = int(time.time())
    version = "0.1.0"
    
    kubernetes = os.getenv('KUBERNETES_SERVICE_HOST') is not None

    response = {
        "version": version,
        "date": current_time,
        "kubernetes": kubernetes
    }
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def query_health():
    """
    Query health status
    ---
    tags:
      - health
    responses:
      200:
        description: OK
        schema:
          id: HealthStatus
          properties:
            status:
              type: string
    """
    return jsonify({"status": "healthy"})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://leyline_api:Jkikow6GGtq==@localhost:5432/leyline_dev'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the domain_lookup model
class DomainLookup(db.Model):
    __tablename__ = 'domain_lookup_logs'
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False, unique=True)
    ipv4_addresses = db.Column(db.Text, nullable=False)  # Store as comma-separated string
    lookup_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, domain, ipv4_addresses):
        self.domain = domain
        self.ipv4_addresses = ipv4_addresses

    def to_dict(self):
        return {
            "domain": self.domain,
            "ipv4_addresses": self.ipv4_addresses,
            "lookup_date": self.lookup_date.isoformat()
        }

@app.route('/v1/history', methods=['GET'])
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
          id: DomainLookup
          properties:
            items:
              type: array
      400:
        description: Bad Request
        schema:
          id: error
          properties:
            items:
              type: string
    """
    history = DomainLookup.query.order_by(DomainLookup.lookup_date.desc()).limit(20).all()

    if not history:
        return jsonify({"message": "No history found"}), 404

    response = []
    response = [entry.to_dict() for entry in history]

    return jsonify(response)

@app.route('/v1/tools/lookup', methods=['GET'])
def lookup_domain():
    """
    Lookup domain and return all IPv4 addresses
    ---
    tags:
      - tools
    responses:
      200:
        description: OK
        schema:
          id: DomainLookup
          properties:
            items:
              type: array
      400:
        description: Bad Request
        schema:
          id: error
          properties:
            items:
              type: string
      404:
        description: Not Found
        schema:
          id: error
          properties:
            items:
              type: string
    """
    domain = request.args.get('domain')
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400

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

        response = {
            "domain": domain,
            "ipv4_addresses": ipv4_addresses
        }
        
        return jsonify(response)
    except socket.gaierror:
        return jsonify({"error": "Invalid domain or unable to resolve domain"}), 400


@app.route('/v1/tools/validate', methods=['POST'])
def validate_ipv4():
    """
    Simple IP validation
    ---
    tags:
      - tools
    responses:
      200:
        description: OK
        schema:
          id: DomainLookup
          properties:
            items:
              type: array
      400:
        description: Bad Request
        schema:
          id: error
          properties:
            items:
              type: string
    """
    data = request.json
    if not data or 'ip' not in data:
        return jsonify({"error": "IP parameter is required"}), 400

    ip = data['ip']

    try:
        # Validate if the input is a valid IPv4 address
        ip_obj = ipaddress.ip_address(ip)
        is_valid = isinstance(ip_obj, ipaddress.IPv4Address)
    except ValueError:
        is_valid = False

    response = {
        "ip": ip,
        "valid_ipv4": is_valid
    }
    
    return jsonify(response), 200

# Define Prometheus metrics
registry = CollectorRegistry()
request_count = Gauge('flask_app_requests_total', 'Total number of requests', registry=registry)
request_duration = Gauge('flask_app_request_duration_seconds', 'Duration of requests in seconds', registry=registry)

@app.before_request
def before_request():
    request_count.inc()  # Increment the request count for each incoming request

@app.route('/metrics')
def metrics():
    # Generate and return metrics in Prometheus format
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    with app.app_context():
        # Create all tables defined by SQLAlchemy models
        db.create_all()
    app.run(debug=True, port=3000)
