import os

class Config:
    # مفتاح التشفير
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

    # قاعدة البيانات
    db_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")
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
