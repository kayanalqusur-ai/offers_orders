import os
from datetime import datetime
from functools import wraps
import uuid
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import current_app

from extensions import db, migrate
import boto3
from config import Config
from flask_babel import Babel, format_number

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import JSON
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from extensions import db
def create_app():
    app = Flask(__name__)
    ...
    db.init_app(app)
    migrate.init_app(app, db)
    return app



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


try:
    from dotenv import load_dotenv
    dotenv_path = "/etc/secrets/aws.env"  # مسار Secret File في Render
    load_dotenv(dotenv_path)
except Exception:
    pass

def allowed_file(filename):
    """التأكد من أن الملف مسموح بصيغته"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def s3_client():
    """
    إرجاع عميل S3 باستخدام إعدادات المشروع.
    يتحقق من وجود المتغيرات قبل الاستخدام.
    """
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID') or current_app.config.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY') or current_app.config.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION') or current_app.config.get('AWS_REGION')

    if not aws_access_key or not aws_secret_key or not aws_region:
        raise RuntimeError("AWS credentials or region not configured!")

    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

def upload_file_to_s3(file):
    return save_file(file)


def save_file(file):
    """
    رفع ملف إلى S3 وإرجاع الرابط المباشر.
    يرجع None إذا لم يكن هناك ملف أو صيغة غير مسموح بها.
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        return None

    try:
        client = s3_client()
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        client.upload_fileobj(
            file,
            os.environ.get('AWS_BUCKET_NAME') or current_app.config.get('AWS_BUCKET_NAME'),
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type
            }
        )

        url = f"https://{os.environ.get('AWS_BUCKET_NAME') or current_app.config.get('AWS_BUCKET_NAME')}.s3.{os.environ.get('AWS_REGION') or current_app.config.get('AWS_REGION')}.amazonaws.com/{unique_filename}"
        return url

    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def remove_files(file_list):
    """
    حذف ملفات من S3 باستخدام روابطها.
    file_list: قائمة روابط الصور
    """
    try:
        client = s3_client()
        bucket_name = os.environ.get('AWS_BUCKET_NAME') or current_app.config.get('AWS_BUCKET_NAME')
        for url in file_list:
            key = url.split('/')[-1]  # استخراج اسم الملف من الرابط
            try:
                client.delete_object(Bucket=bucket_name, Key=key)
            except Exception as e:
                print(f"Error deleting {key}: {e}")
    except Exception as e:
        print(f"S3 client not configured properly: {e}")

# ================== تهيئة التطبيق ==================
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your_secret_key_here")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "sqlite:///database.db"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# مجلد رفع الملفات
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ربط db & migrate
db.init_app(app)
migrate.init_app(app, db)

# استيراد الموديلات بعد db
from models import Employee, Log, Property, RentalOffer, SaleOffer, Orders

# ================== تهيئة تسجيل الدخول ==================
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))


babel = Babel(app)

@app.template_filter("price")
def format_price(value):
    if value is None:
        return ""
    return format_number(value, locale="de_DE")  # يعطي 1.000.000




# ================== صلاحيات ==================
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(permission):
                flash("🚫 ليس لديك صلاحية", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_unique_filename(filename):
    """إرجاع اسم ملف فريد باستخدام UUID"""
    name = secure_filename(filename)
    return f"{uuid.uuid4().hex}_{name}"

# ================== تسجيل الدخول ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = Employee.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"مرحباً {user.username}", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("اسم المستخدم أو كلمة المرور خاطئة", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج ✅", "success")
    return redirect(url_for('login'))


# ================== لوحة التحكم ==================
@app.route('/')
@login_required
def dashboard():
    try:
        employees_count = Employee.query.count()
        rentalm_offers_count = RentalOffer.query.filter_by(district='وسط').count()
        rentalw_offers_count = RentalOffer.query.filter_by(district='جنوب').count()
        salesm_offers_count = SaleOffer.query.filter_by(district='وسط').count()
        salesw_offers_count = SaleOffer.query.filter_by(district='جنوب').count()
        orders_count = Orders.query.count()
    except Exception as e:
        return f"خطأ في dashboard: {e}", 500

    return render_template(
        'dashboard.html',
        employees_count=employees_count,
        rentalm_offers_count=rentalm_offers_count,
        rentalw_offers_count=rentalw_offers_count,
        salesm_offers_count=salesm_offers_count,
        salesw_offers_count=salesw_offers_count,
        orders_count=orders_count
    )


# ================== الصلاحيات ==================
AVAILABLE_PERMISSIONS = [
    ('logs_view', 'عرض السجلات'),
    ('list_employees', 'عرض الموظفين'),
    ('add_employee', 'إضافة موظف'),
    ('edit_employee', 'تعديل الموظف'),
    ('delete_employee', 'حذف الموظف'),
    ('rentalm_offers_view', 'عرض عروض الإيجار وسط'),
    ('rentalm_offers_add', 'إضافة عرض إيجار وسط'),
    ('rentalm_offers_edit', 'تعديل عرض إيجار وسط'),
    ('rentalm_offers_delete', 'حذف عرض إيجار وسط'),
    ('rentalw_offers_view', 'عرض عروض الإيجار جنوب'),
    ('rentalw_offers_add', 'إضافة عرض إيجار جنوب'),
    ('rentalw_offers_edit', 'تعديل عرض إيجار جنوب'),
    ('rentalw_offers_delete', 'حذف عرض إيجار جنوب'),
    ('salesm_offers_view', 'عرض عروض البيع وسط'),
    ('salesm_offers_add', 'إضافة عرض بيع وسط'),
    ('salesm_offers_edit', 'تعديل عرض بيع وسط'),
    ('salesm_offers_delete', 'حذف عرض بيع وسط'),
    ('salesw_offers_view', 'عرض عروض البيع جنوب'),
    ('salesw_offers_add', 'إضافة عرض بيع جنوب'),
    ('salesw_offers_edit', 'تعديل عرض بيع جنوب'),
    ('salesw_offers_delete', 'حذف عرض بيع جنوب'),
    ('orders_view', 'عرض الطلبات'),
    ('orders_add', 'إضافة طلب'),
    ('orders_edit', 'تعديل الطلب'),
    ('orders_delete', 'حذف الطلب')
]


# ================== دوال مساعدة ==================
def add_log(action):
    """إضافة سجل نشاطات المستخدم"""
    log = Log(user=current_user.username, action=action)
    db.session.add(log)
    db.session.commit()


# ================== إدارة الموظفين ==================
@app.route('/employees')
@login_required
@permission_required('list_employees')
def list_employees():
    employees = Employee.query.all()
    return render_template(
        'employees/list.html',
        employees=employees,
        available_permissions=AVAILABLE_PERMISSIONS,
        employee=None
    )


# ------------------ إضافة موظف جديد ------------------
@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_employee')
def add_employee():
    if request.method == 'POST':
        name = request.form['name'].strip()
        role = request.form['role'].strip()
        username = request.form['username'].strip()
        password = request.form.get('password', '').strip()
        permissions_list = request.form.getlist('permissions[]')

        if not password:
            flash("كلمة المرور مطلوبة لإضافة موظف جديد", "danger")
            return redirect(url_for('add_employee'))

        if Employee.query.filter_by(username=username).first():
            flash("اسم المستخدم موجود بالفعل، اختر اسم آخر", "danger")
            return redirect(url_for('add_employee'))

        new_employee = Employee(
            name=name,
            role=role,
            username=username,
            password=generate_password_hash(password)
        )
        new_employee.set_permissions(permissions_list)
        db.session.add(new_employee)
        db.session.commit()

        flash("تمت إضافة الموظف بنجاح ✅", "success")
        add_log(f"إضافة موظف جديد: {name}")
        return redirect(url_for('list_employees'))

    return render_template(
        'employees/list.html',
        available_permissions=AVAILABLE_PERMISSIONS
    )


# ------------------ تعديل موظف ------------------
@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_employee')
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        employee.name = request.form['name'].strip()
        employee.role = request.form['role'].strip()
        employee.username = request.form['username'].strip()

        # تحديث كلمة المرور إذا تم إدخالها
        password = request.form.get('password', '').strip()
        if password:
            employee.password = generate_password_hash(password)

        # تحديث الصلاحيات
        selected_perms = request.form.getlist('permissions[]')
        employee.set_permissions(selected_perms)
        
        db.session.commit()

        # إذا الموظف المعدل هو نفسه المستخدم الحالي، حدث الجلسة
        if current_user.id == employee.id:
            login_user(employee, fresh=True)

        flash('تم تعديل الموظف بنجاح ✅', 'success')
        add_log(f"تعديل الموظف: {employee.name}")
        return redirect(url_for('list_employees'))
    
    return render_template(
        'employees/edit.html', 
        employee=employee, 
        available_permissions=AVAILABLE_PERMISSIONS
    )


# ------------------ حذف موظف ------------------
@app.route('/employees/delete/<int:employee_id>', methods=['POST'])
@login_required
@permission_required('delete_employee')
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if employee.id == current_user.id:
        flash("لا يمكنك حذف حسابك الخاص", "danger")
        return redirect(url_for('list_employees'))

    name = employee.name
    db.session.delete(employee)
    db.session.commit()

    add_log(f"حذف الموظف: {name}")
    flash("تم حذف الموظف بنجاح ✅", "success")
    return redirect(url_for('list_employees'))


# ================== عروض الإيجار - وسط ==================
@app.route('/rentalm_offers')
@login_required
@permission_required('rentalm_offers_view')
def rentalm_offers():
    offers = RentalOffer.query.filter_by(district='وسط').order_by(RentalOffer.created_at.desc()).all()
    return render_template('rental_offers/list.html', offers=offers, district='وسط', district_name='وسط')


@app.route('/rentalm_offers/add', methods=['GET', 'POST'])
@login_required
@permission_required('rentalm_offers_add')
def add_rentalm_offer():
    if request.method == 'POST':
        images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    images.append(url)

        offer = RentalOffer(
            unit_type=request.form['unit_type'].strip()[:200],
            floor=request.form['floor'].strip()[:100],
            area=float(request.form['area']) if request.form.get('area') else None,
            price=float(request.form['price']) if request.form.get('price') else None,
            details=request.form.get('details', '').strip()[:2100],
            owner_type = request.form.get("owner_type") or request.form.get("owner_type_other"),
            location=request.form.get('location', '').strip()[:2100],
            marketer=request.form.get('marketer', '').strip()[:100],
            notes=request.form.get('notes', '').strip()[:2100],
            status=request.form['status'].strip()[:50],
            district='وسط',
            images=images
        )
        db.session.add(offer)
        db.session.commit()
  
        add_log(f"إضافة عرض إيجار وسط: {offer.unit_type}")
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('rentalm_offers'))

    return render_template('rental_offers/add.html', district='وسط', district_name='وسط')


@app.route('/rentalm_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalm_offers_edit')
def edit_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    if request.method == 'POST':
        # معالجة الصور
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    new_images.append(url)

        # إذا تم رفع صور جديدة فقط
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images

        # تحديث باقي بيانات العرض دائمًا
        offer.unit_type = request.form.get('unit_type', '').strip()[:200]
        offer.floor = request.form.get('floor', '').strip()[:100]
        offer.area = float(request.form['area']) if request.form.get('area') else None
        offer.price = float(request.form['price']) if request.form.get('price') else None
        offer.details = request.form.get('details', '').strip()[:2100]
        offer.owner_type = request.form.get("owner_type") or request.form.get("owner_type_other")
        offer.location = request.form.get('location', '').strip()[:2100]
        offer.marketer = request.form.get('marketer', '').strip()[:100]
        offer.notes = request.form.get('notes', '').strip()[:2100]
        offer.status = request.form.get('status', '').strip()[:50]

        db.session.commit()

        add_log(f"تعديل عرض إيجار وسط: {offer.unit_type}")
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('rentalm_offers'))

    # عند GET فقط
    return render_template('rental_offers/add.html', offer=offer, district='وسط', district_name='وسط')


@app.route('/rentalm_offers/delete/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalm_offers_delete')
def delete_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    # حذف الصور المرفقة
    remove_files(offer.images or [])

    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()

    add_log(f"حذف عرض إيجار وسط: {unit_type}")
    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('rentalm_offers'))


# ================== تفاصيل الإيجار (موحّد) ==================
@app.route('/rental_offers/<district>/<int:offer_id>')
@login_required
def rental_offer_detail(district, offer_id):
    offer = RentalOffer.query.filter_by(id=offer_id, district=district).first_or_404()
    # لتسهيل زر الرجوع في القالب
    back_endpoint = 'rentalm_offers' if district == 'وسط' else 'rentalw_offers'
    return render_template(
        "rental_offers/detail.html",
        offer=offer,
        district=district,
        district_name='وسط' if district == 'وسط' else 'جنوب',
        back_endpoint=back_endpoint
    )


# ----- توافق مع قوالب/روابط قديمة (Aliases) -----
@app.route('/rentalm_offers/<int:offer_id>')
@login_required
def rentalm_offer_detail(offer_id):
    # إعادة توجيه للـ endpoint الموحّد
    return redirect(url_for('rental_offer_detail', district='وسط', offer_id=offer_id))

@app.route('/rentalw_offers/<int:offer_id>')
@login_required
def rentalw_offer_detail(offer_id):
    # إعادة توجيه للـ endpoint الموحّد
    return redirect(url_for('rental_offer_detail', district='جنوب', offer_id=offer_id))


# ================== عروض الإيجار - جنوب ==================
@app.route('/rentalw_offers')
@login_required
@permission_required('rentalw_offers_view')
def rentalw_offers():
    offers = RentalOffer.query.filter_by(district='جنوب').order_by(RentalOffer.created_at.desc()).all()
    return render_template('rental_offers/list.html', offers=offers, district='جنوب', district_name='جنوب')


@app.route('/rentalw_offers/add', methods=['GET', 'POST'])
@login_required
@permission_required('rentalw_offers_add')
def add_rentalw_offer():
    if request.method == 'POST':
        images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    images.append(url)
        offer = RentalOffer(
            unit_type=request.form['unit_type'].strip()[:200],
            floor=request.form['floor'].strip()[:100],
            area=float(request.form['area']) if request.form.get('area') else None,
            price=float(request.form['price']) if request.form.get('price') else None,
            details=request.form.get('details', '').strip()[:2100],
            owner_type = request.form.get("owner_type") or request.form.get("owner_type_other"),
            location=request.form.get('location', '').strip()[:2100],
            marketer=request.form.get('marketer', '').strip()[:100],
            notes=request.form.get('notes', '').strip()[:2100],
            status=request.form['status'].strip()[:50],
            district='جنوب',
            images=images
        )

        db.session.add(offer)
        db.session.commit()

        add_log(f"إضافة عرض إيجار جنوب: {offer.unit_type}")
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('rentalw_offers'))

    return render_template('rental_offers/add.html', district='جنوب', district_name='جنوب')


@app.route('/rentalw_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalw_offers_edit')
def edit_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    if request.method == 'POST':
        # معالجة الصور
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    new_images.append(url)

        # إذا تم رفع صور جديدة فقط
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images

        offer.unit_type = request.form['unit_type'].strip()[:200]
        offer.floor = request.form['floor'].strip()[:100]
        offer.area = float(request.form['area']) if request.form.get('area') else None
        offer.price = float(request.form['price']) if request.form.get('price') else None
        offer.details = request.form.get('details', '').strip()[:2100]
        offer.owner_type = request.form.get("owner_type") or request.form.get("owner_type_other")
        offer.location = request.form.get('location', '').strip()[:2100]
        offer.marketer = request.form.get('marketer', '').strip()[:100]
        offer.notes = request.form.get('notes', '').strip()[:2100]
        offer.status = request.form['status'].strip()[:50]
        offer.updated_at = datetime.utcnow()

        db.session.commit()
        add_log(f"تعديل عرض إيجار جنوب: {offer.unit_type}")
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('rentalw_offers'))

    return render_template('rental_offers/add.html', offer=offer, district='جنوب', district_name='جنوب')


@app.route('/rentalw_offers/delete/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalw_offers_delete')
def delete_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    # حذف الصور المرفقة
    remove_files(offer.images or [])

    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()

    add_log(f"حذف عرض إيجار [جنوب]: {unit_type}")
    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('rentalw_offers'))


# ================== عروض البيع - وسط ==================
@app.route('/salesm_offers')
@login_required
@permission_required('salesm_offers_view')
def salesm_offers():
    offers = SaleOffer.query.filter_by(district='وسط').order_by(SaleOffer.created_at.desc()).all()
    return render_template('sale_offers/list.html', offers=offers, district='وسط', district_name='وسط')


@app.route('/salesm_offers/add', methods=['GET', 'POST'])
@login_required
@permission_required('salesm_offers_add')
def add_salesm_offer():
    if request.method == 'POST':
        images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    images.append(url)

        offer = SaleOffer(
            unit_type=request.form.get('unit_type', '').strip()[:200],
            floor=request.form.get('floor', '').strip()[:200],
            front=request.form.get('front', '').strip()[:200],
            street=request.form.get('street', '').strip()[:200],
            area=float(request.form['area']) if request.form.get('area') else None,
            price=float(request.form['price']) if request.form.get('price') else None,
            sale_limit=float(request.form['sale_limit']) if request.form.get('sale_limit') else None,
            details=request.form.get('details', '').strip()[:2100],
            owner_type = request.form.get("owner_type") or request.form.get("owner_type_other"),
            location=request.form.get('location', '').strip()[:2100],
            marketer=request.form.get('marketer', '').strip()[:100],
            status=request.form.get('status', '').strip()[:50],
            notes=request.form.get('notes', '').strip()[:2100],
            district='وسط',
            images=images,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=current_user.username
        )
        db.session.add(offer)
        db.session.commit()
        add_log(f"إضافة عرض بيع وسط: {offer.unit_type}")
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('salesm_offers'))

    return render_template('sale_offers/add.html', district='وسط', district_name='وسط')

# ================= تعديل عرض بيع =================
@app.route('/salesm_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('salesm_offers_edit')
def edit_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)

    if request.method == 'POST':
        # معالجة الصور
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    new_images.append(url)

        # إذا تم رفع صور جديدة فقط
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images

        offer.unit_type = request.form['unit_type'].strip()[:200]
        offer.floor = request.form['floor'].strip()[:200]
        offer.front = request.form.get('front','').strip()[:200]
        offer.street = request.form.get('street','').strip()[:200]
        offer.area = float(request.form['area']) if request.form.get('area') else None
        offer.price = float(request.form['price']) if request.form.get('price') else None
        offer.sale_limit = float(request.form['sale_limit']) if request.form.get('sale_limit') else None
        offer.details = request.form.get('details','').strip()[:1000]
        offer.owner_type = request.form.get("owner_type") or request.form.get("owner_type_other")
        offer.location = request.form.get('location','').strip()[:2100]
        offer.marketer = request.form.get('marketer','').strip()[:100]
        offer.notes = request.form.get('notes','').strip()[:2100]
        offer.status = request.form['status'].strip()[:50]
        offer.updated_at = datetime.utcnow()

        db.session.commit()
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('salesm_offers'))

    return render_template('sale_offers/add.html', offer=offer, district='وسط', district_name='وسط')

@app.route('/salesm_offers/delete/<int:offer_id>',  methods=['POST', 'GET'])
@login_required
@permission_required('salesm_offers_delete')
def delete_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)

    # حذف الصور المرفقة
    remove_files(offer.images or [])

    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()

    log = Log(user=current_user.username, action=f"حذف عرض بيع وسط: {unit_type}")
    db.session.add(log)
    db.session.commit()

    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('salesm_offers'))


@app.route("/sales_offers/<district>/<int:offer_id>")
def sales_offer_detail(district, offer_id):
    offer = SaleOffer.query.filter_by(id=offer_id, district=district).first_or_404()
    return render_template(
        "sale_offers/detail.html",
        offer=offer,
        district=district,
        district_name="المنطقة الوسطى" if district == "وسط" else "المنطقة الجنوبية"
    )


# ================== عروض البيع - جنوب ==================
@app.route('/salesw_offers')
@login_required
@permission_required('salesw_offers_view')
def salesw_offers():
    offers = SaleOffer.query.filter_by(district='جنوب').order_by(SaleOffer.created_at.desc()).all()
    return render_template('sale_offers/list.html', offers=offers, district='جنوب', district_name='جنوب')


@app.route('/salesw_offers/add', methods=['GET', 'POST'])
@login_required
@permission_required('salesw_offers_add')
def add_salesw_offer():
    if request.method == 'POST':
        images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    images.append(url)

        offer = SaleOffer(
            unit_type=request.form['unit_type'][200:],
            district='جنوب',
            area=float(request.form['area']) if request.form['area'] else None,
            floor=request.form['floor'][:200],
            front=request.form['front'][:200],
            street=request.form['street'][:200],
            price=float(request.form['price']) if request.form['price'] else None,
            sale_limit=float(request.form['sale_limit']) if request.form['sale_limit'] else None,
            location=request.form['location'][:2100],
            details=request.form['details'][:2100],
            marketer=request.form['marketer'][:100],
            owner_type=request.form.get("owner_type") or request.form.get("owner_type_other"),
            status=request.form['status'][:50],
            images=images,
            notes=request.form['notes'][:2100],
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
   )

        db.session.add(offer)
        db.session.commit()

        log = Log(user=current_user.username, action=f"إضافة عرض بيع جنوب: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()

        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('salesw_offers'))

    return render_template('sale_offers/add.html', district='جنوب', district_name='جنوب')


@app.route('/salesw_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('salesw_offers_edit')
def edit_salesw_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)

    if request.method == 'POST':
        # معالجة الصور
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                url = upload_file_to_s3(file)
                if url:
                    new_images.append(url)

        # إذا تم رفع صور جديدة فقط
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images

        offer.unit_type = (request.form.get('unit_type') or '')[:200]
        offer.area = float(request.form['area']) if request.form.get('area') else None
        offer.floor = (request.form.get('floor') or '')[:200]
        offer.front = (request.form.get('front') or '')[:200]
        offer.street = (request.form.get('street') or '')[:200]
        offer.price = float(request.form['price']) if request.form.get('price') else None
        offer.sale_limit = float(request.form['sale_limit']) if request.form.get('sale_limit') else None
        offer.location = (request.form.get('location') or '')[:2100]
        offer.details = (request.form.get('details') or '')[:2100]
        offer.marketer = (request.form.get('marketer') or '')[:100]
        offer.owner_type = (request.form.get("owner_type") or request.form.get("owner_type_other"))[:50]
        offer.status = (request.form.get('status') or '')[:50]
        offer.notes = (request.form.get('notes') or '')[:2100]

# تحديث وقت التعديل
        offer.updated_at = datetime.utcnow()

        db.session.commit()


        log = Log(user=current_user.username, action=f"تعديل عرض بيع جنوب: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()

        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('salesw_offers'))

    return render_template('sale_offers/add.html', offer=offer, district='جنوب', district_name='جنوب')


@app.route('/salesw_offers/delete/<int:offer_id>', methods=['POST', 'GET'])
@login_required
@permission_required('salesw_offers_delete')
def delete_salesw_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)

    # حذف الصور المرفقة
    remove_files(offer.images or [])

    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()

    log = Log(user=current_user.username, action=f"حذف عرض بيع جنوب: {unit_type}")
    db.session.add(log)
    db.session.commit()

    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('salesw_offers'))

# ================== الطلبات ==================
@app.route('/orders')
@login_required
@permission_required('orders_view')
def orders():
    all_orders = Orders.query.order_by(Orders.created_at.desc()).all()
    return render_template('orders/list.html', requests=all_orders)


@app.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()[:200]
        unit_type = request.form.get('unit_type', '').strip()[:200]
        area = request.form.get('area', '').strip()[:200]
        price = request.form.get('price', '').strip()[:200]
        location = request.form.get('location', '').strip()[:200]
        phone = request.form.get('phone', '').strip()[:200]
        marketer = request.form.get('marketer', '').strip()[:100]
        notes = request.form.get('notes', '').strip()[:2100]

        if not customer_name or not unit_type:
            flash("يرجى ملء جميع الحقول المطلوبة", "danger")
            return redirect(url_for('add_request'))

        new_request = Orders(
            customer_name=customer_name,
            unit_type=unit_type,
            area=area,
            price=price,
            location=location,
            phone=phone,
            marketer=marketer,
            notes=notes
        )
        db.session.add(new_request)
        db.session.commit()
        add_log(f"إضافة طلب جديد: {customer_name}")
        flash("تم حفظ الطلب بنجاح ✅", "success")
        return redirect(url_for('orders'))

    return render_template('orders/add.html')


@app.route('/edit_request/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('orders_edit')
def edit_request(id):
    req = Orders.query.get_or_404(id)
    if request.method == 'POST':
        req.unit_type = request.form['unit_type'].strip()[:200]
        req.area = request.form['area'].strip()[:200]
        req.price = request.form['price'].strip()[:200]
        req.location = request.form['location'].strip()[:200]
        req.phone = request.form['phone'].strip()[:200]
        req.marketer = request.form['marketer'].strip()[:200]
        req.notes = request.form['notes'].strip()[:2100]
        db.session.commit()
        add_log(f"تعديل الطلب: {req.customer_name}")
        flash("تم تعديل الطلب ✏️", "success")
        return redirect(url_for('orders'))

    return render_template('orders/edit.html', req=req)


@app.route('/delete_request/<int:id>', methods=['POST'])
@login_required
@permission_required('orders_delete')
def delete_request(id):
    req = Orders.query.get_or_404(id)
    db.session.delete(req)
    db.session.commit()
    add_log(f"حذف الطلب: {req.customer_name}")
    flash("تم حذف الطلب 🗑", "danger")
    return redirect(url_for('orders'))


# ================== السجلات ==================
@app.route('/view_logs')
@login_required
@permission_required('logs_view')
def view_logs():
    logs_list = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
    return render_template('logs.html', logs=logs_list)


# ================== رفع الملفات ==================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ================== تشغيل التطبيق ==================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ جميع الجداول تم إنشاؤها بنجاح")

        # إنشاء المستخدم الأول إذا لم يوجد
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

    # تشغيل السيرفر
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)