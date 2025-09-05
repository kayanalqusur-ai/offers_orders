from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class Employee(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    permissions = db.Column(db.Text, default='[]')  # تخزين الصلاحيات كـ JSON
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
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Property(db.Model):
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
    images = db.Column(db.PickleType)
    district = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SaleOffer(db.Model):
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
    images = db.Column(db.PickleType)
    notes = db.Column(db.Text)             
    created_by = db.Column(db.String(100))      
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RentalMOffer(db.Model):
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
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    image4 = db.Column(db.String(200))
    image5 = db.Column(db.String(200))

class RentalWOffer(db.Model):
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
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    image4 = db.Column(db.String(200))
    image5 = db.Column(db.String(200))
    
class Orders(db.Model):
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
