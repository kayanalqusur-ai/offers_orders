# config.py
import os
from dotenv import load_dotenv
class Config:
    # مفتاح التشفير
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


    # قاعدة البيانات
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://offers_orders:qkiEgdvonowQqG5psQD4Rik2QvDdV4SA@dpg-d2t7pimuk2gs73cjkkdg-a.oregon-postgres.render.com/offers_orders"
    )
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url

    # تعطيل تتبع التعديلات
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # مسار رفع الملفات
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "static/uploads")

    # الحد الأقصى لحجم الملفات المرفوعة (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # وضع التطوير
    DEBUG = os.environ.get("DEBUG", "False").lower() in ["true", "1", "t"]

    # المنفذ
    PORT = int(os.environ.get("PORT", 5000))



