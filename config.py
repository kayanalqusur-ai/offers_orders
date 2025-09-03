import os
class Config:
    # مفتاح التشفير (خذه من Environment Variable في Render)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

    # قاعدة البيانات (PostgreSQL في Render - SQLite محلياً)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///database.db")

    # تعطيل تتبع التعديلات (يستهلك موارد زيادة)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # مسار رفع الملفات
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "static/uploads")

    # الحد الأقصى لحجم الملفات المرفوعة
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    # وضع التطوير (ممكن تتحكم فيه من Render)
    DEBUG = os.environ.get("DEBUG", "False").lower() in ["true", "1", "t"]

    # المنفذ (Render يستخدم PORT من Environment Variable)
    PORT = int(os.environ.get("PORT", 5000))
