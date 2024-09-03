"""
Application's database models
"""
import ast
from datetime import datetime
from flask import request
import time

from src import db

# Define the domain_lookup model
class DomainLookup(db.Model):  # pylint: disable=too-few-public-methods
    """
    Declare Domain lookup model class
    """
    __tablename__ = 'domain_lookup_logs'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    domain = db.Column(db.String(255), nullable=False, unique=True)
    ipv4_addresses = db.Column(db.Text, nullable=False)  # Store as comma-separated string
    lookup_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, domain, ipv4_addresses):
        self.domain = domain
        self.ipv4_addresses = ipv4_addresses

    def to_dict(self):
        """
        Help to deserialize model data
        """
        addresses_list = ast.literal_eval(self.ipv4_addresses)
        return {
            "queryID": self.id,
            "domain": self.domain,
            "addresses": [{"ip": ip, "queryID": self.id} for ip in addresses_list],
            "created_time": int(time.mktime(self.lookup_date.timetuple())),
            "client_ip": request.remote_addr
        }
