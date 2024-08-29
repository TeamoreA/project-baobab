from datetime import datetime

from src import db

# Define the domain_lookup model
class DomainLookup(db.Model):
    __tablename__ = 'domain_lookup_logs'
    id = db.Column(db.Integer, primary_key=True, unique=True)
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
    