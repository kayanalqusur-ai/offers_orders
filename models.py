from extensions import db
from flask_login import UserMixin
from datetime import datetime
import json
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import ARRAY


class Employee(db.Model, UserMixin):
    __tablename__ = 'employee'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    permissions = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_permissions(self, perms_list):
        self.permissions = json.dumps([str(p) for p in perms_list])

    def get_permissions(self):
        try:
            perms = json.loads(self.permissions or '[]')
            return [str(p) for p in perms] if isinstance(perms, list) else []
        except:
            return []

    def has_permission(self, perm):
        return str(perm) in self.get_permissions()


class Log(db.Model):
    __tablename__ = 'log'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Property(db.Model):
    __tablename__ = 'property'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(100))
    district = db.Column(db.String(100))
    area = db.Column(db.Float)
    front = db.Column(db.String(50))
    street = db.Column(db.String(100))
    owner_status = db.Column(db.String(50))
    images = db.Column(db.PickleType)  # قائمة بالصور


class RentalOffer(db.Model):
    __tablename__ = 'rental_offer'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    property = db.relationship("Property", backref="rental_offers")
    unit_type = db.Column(db.String(100))
    floor = db.Column(db.String(50))
    area = db.Column(db.Float)
    price = db.Column(db.Float)
    detalis = db.Column(db.String(50))
    owner_type = db.Column(db.String(50))
    location = db.Column(db.String(200))
    marketer = db.Column(db.String(100))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50))
    images = db.Column(ARRAY(db.String), default=[])
    district = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SaleOffer(db.Model):
    __tablename__ = 'sale_offer'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    unit_type = db.Column(db.String(100))
    district = db.Column(db.String(50))
    area = db.Column(db.Float)
    floor = db.Column(db.String(50))
    front = db.Column(db.String(50))
    street = db.Column(db.String(50))
    price = db.Column(db.Float)
    sale_limit = db.Column(db.Float)
    location = db.Column(db.String(300))
    detalis = db.Column(db.Text)
    marketer = db.Column(db.String(100))
    owner_type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    images = db.Column(ARRAY(db.String), default=[])
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RentalMOffer(db.Model):
    __tablename__ = 'rental_m_offer'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    unit_type = db.Column(db.String(100))
    area = db.Column(db.Float)
    floor = db.Column(db.String(50))
    detalis = db.Column(db.Text)
    price = db.Column(db.Float)
    location = db.Column(db.String(200))
    owner_type = db.Column(db.String(50))
    marketer = db.Column(db.String(100))
    status = db.Column(db.String(50))
    notes = db.Column(db.Text)
    images = db.Column(ARRAY(db.String), default=[])



class RentalWOffer(db.Model):
    __tablename__ = 'rental_w_offer'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    unit_type = db.Column(db.String(100))
    area = db.Column(db.Float)
    floor = db.Column(db.String(50))
    detalis = db.Column(db.Text)
    price = db.Column(db.Float)
    location = db.Column(db.String(200))
    owner_type = db.Column(db.String(50))
    marketer = db.Column(db.String(100))
    status = db.Column(db.String(50))
    notes = db.Column(db.Text)
    images = db.Column(ARRAY(db.String), default=[])



class Orders(db.Model):
    __tablename__ = 'orders'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    unit_type = db.Column(db.String(100), nullable=False)
    area = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    marketer = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
