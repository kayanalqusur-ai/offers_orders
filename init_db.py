from main import app, db   # استدعاء التطبيق وقاعدة البيانات
from models import Employee   # استدعاء الموديل
from werkzeug.security import generate_password_hash

with app.app_context():
    # إنشاء كل الجداول
    db.create_all()

    # إنشاء مستخدم admin إذا لم يكن موجود
    if Employee.query.count() == 0:
        admin = Employee(
            name="المدير العام",
            role="مدير",
            username="admin",
            password=generate_password_hash("admin123")
        )
        admin.set_permissions([
            'logs_view', 'list_employees', 'add_employee', 'edit_employee', 'delete_employee',
            'rentalm_offers_view', 'rentalm_offers_add', 'rentalm_offers_edit', 'rentalm_offers_delete',
            'rentalw_offers_view', 'rentalw_offers_add', 'rentalw_offers_edit', 'rentalw_offers_delete',
            'salesm_offers_view', 'salesm_offers_add', 'salesm_offers_edit', 'salesm_offers_delete',
            'salesw_offers_view', 'salesw_offers_add', 'salesw_offers_edit', 'salesw_offers_delete',
            'orders_view', 'orders_add', 'orders_edit', 'orders_delete'
        ])
        db.session.add(admin)
        db.session.commit()
        print("✅ تم إنشاء المستخدم الأول: admin / admin123")
    else:
        print(" يوجد مستخدمين بالفعل في قاعدة البيانات")
