from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

# ================== نموذج الموظف ==================
class Employee(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    permissions = db.Column(db.Text, default='[]')  # تخزين الصلاحيات بصيغة JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_permissions(self, perms_list):
        """تعيين الصلاحيات وحفظها كـ JSON"""
        self.permissions = json.dumps(perms_list or [])

    def get_permissions(self):
        """إرجاع قائمة الصلاحيات"""
        try:
            return json.loads(self.permissions or '[]')
        except:
            return []

    def has_permission(self, perm):
        """التحقق من وجود صلاحية معينة"""
        return perm in self.get_permissions()


# ================== نموذج عروض الإيجار ==================


# ================== نموذج عروض البيع ==================
class SaleOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(100))
    area = db.Column(db.Float)
    floor = db.Column(db.String(50))
    details = db.Column(db.Text)
    price = db.Column(db.Float)
    location = db.Column(db.String(300))
    marketer = db.Column(db.String(100))
    notes = db.Column(db.Text)
    image = db.Column(db.String(200))
    district = db.Column(db.String(50))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    


# ================== نموذج سجل العمليات ==================
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
