import os
import json
from fileinput import filename
from click import edit
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

# ================== تهيئة التطبيق ==================
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ================== النماذج ==================
class Employee(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    permissions = db.Column(db.Text, default='[]')  # JSON نصي
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_permissions(self, perms_list):
        """حفظ الصلاحيات كـ JSON نصي"""
        if not isinstance(perms_list, list):
            perms_list = []
        perms_list = [str(p) for p in perms_list]
        self.permissions = json.dumps(perms_list)

    def get_permissions(self):
        """إرجاع قائمة الصلاحيات"""
        try:
            perms = json.loads(self.permissions or '[]')
            if not isinstance(perms, list):
                return []
            return [str(p) for p in perms]
        except json.JSONDecodeError:
            return []

    def has_permission(self, perm):
        """التحقق من وجود صلاحية معينة"""
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
    images = db.Column(db.PickleType)


class RentalOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    property = db.relationship("Property", backref="rental_offers")
    unit_type = db.Column(db.String(100))
    floor = db.Column(db.String(50))
    area = db.Column(db.Float)
    price = db.Column(db.Float)
    detalis = db.Column(db.String(50))  # تم تصحيح الاسم
    owner_type = db.Column(db.String(50))
    location = db.Column(db.String(200))
    marketer = db.Column(db.String(100))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50))  # تم تصحيح Column
    images      = db.Column(db.PickleType)  # لتخزين قائمة الصور
    district = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class SaleOffer(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    unit_type   = db.Column(db.String(100))      
    district    = db.Column(db.String(50))      
    area        = db.Column(db.Float)             
    floor       = db.Column(db.String(50))       
    front       = db.Column(db.String(50))       
    street      = db.Column(db.String(50))      
    price       = db.Column(db.Float)            
    sale_limit  = db.Column(db.Float)            
    location    = db.Column(db.String(300))      
    details     = db.Column(db.Text)             
    marketer    = db.Column(db.String(100))     
    owner_type  = db.Column(db.String(50))        
    status      = db.Column(db.String(50))       
    images      = db.Column(db.PickleType)  # لتخزين قائمة الصور
    notes       = db.Column(db.Text)             
    created_by  = db.Column(db.String(100))      
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


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


# ================== إدارة المستخدم ==================
@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
    flash("تم تسجيل الخروج بنجاح", "info")
    return redirect(url_for('login'))


# ================== Decorator للتحقق من الصلاحيات ==================
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'has_permission') or not current_user.has_permission(permission):
                flash("ليس لديك الصلاحية المطلوبة", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ================== لوحة التحكم ==================
@app.route('/')
@login_required
def dashboard():
    employees_count = Employee.query.count()
    rentalm_offers_count = RentalOffer.query.filter_by(district='وسط').count()
    rentalw_offers_count = RentalOffer.query.filter_by(district='جنوب').count()
    salesm_offers_count = SaleOffer.query.filter_by(district='وسط').count()
    salesw_offers_count = SaleOffer.query.filter_by(district='جنوب').count()
    orders_count = Orders.query.count()

    return render_template(
        'dashboard.html',
        employees_count=employees_count,
        rentalm_offers_count=rentalm_offers_count,
        rentalw_offers_count=rentalw_offers_count,
        salesm_offers_count=salesm_offers_count,
        salesw_offers_count=salesw_offers_count,
        orders_count=orders_count
    )

# ================== إدارة الموظفين ==================


@app.route('/employees', methods=['GET', 'POST'])
@login_required
def list_employees():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form['name'].strip()
        role = request.form['role'].strip()
        username = request.form['username'].strip()
        password = request.form.get('password', '').strip()
        permissions_list = request.form.getlist('permissions[]')

        if employee_id:  # تعديل موظف موجود
            employee = Employee.query.get(int(employee_id))
            if not employee:
                flash("الموظف غير موجود", "danger")
                return redirect(url_for('list_employees'))

            employee.name = name
            employee.role = role
            employee.username = username
            if password:
                employee.password = generate_password_hash(password)

            # تحديث الصلاحيات فقط إذا تم اختيار شيء
            if permissions_list:
                employee.set_permissions(permissions_list)

            flash("تم تحديث بيانات الموظف بنجاح ✅", "success")
            log_action = f"تحديث بيانات الموظف: {name}"

        else:  # إضافة موظف جديد
            if not password:
                flash("كلمة المرور مطلوبة لإضافة موظف جديد", "danger")
                return redirect(url_for('list_employees'))

            new_employee = Employee(
                name=name,
                role=role,
                username=username,
                password=generate_password_hash(password)
            )
            new_employee.set_permissions(permissions_list)
            db.session.add(new_employee)
            flash("تمت إضافة الموظف بنجاح ✅", "success")
            log_action = f"إضافة موظف جديد: {name}"

        db.session.commit()

        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        return redirect(url_for('list_employees'))

    employees = Employee.query.all()
    available_permissions = [
      ('logs', 'عرض السجلات'),
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
    return render_template('employees/list.html', employees=employees, available_permissions=available_permissions, employee=None)


@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employees = Employee.query.all()

    available_permissions = [
        ('logs', 'عرض السجلات'),
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

    if request.method == 'POST':
        # تحديث بيانات الموظف من الفورم
        employee.name = request.form['name'].strip()
        employee.role = request.form['role'].strip()
        employee.username = request.form['username'].strip()
        password = request.form.get('password', '').strip()
        if password:
            employee.password = generate_password_hash(password)

        # تحديث الصلاحيات فقط إذا تم اختيار شيء
        permissions_list = request.form.getlist('permissions[]')
        if permissions_list:
            employee.set_permissions(permissions_list)

        db.session.commit()  # حفظ التغييرات على الموظف أولاً

        # تسجيل العملية في السجلات
        log_action = f"تعديل بيانات الموظف: {employee.name}"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تحديث بيانات الموظف بنجاح ✅", "success")
        return redirect(url_for('list_employees'))

    return render_template(
        'employees/list.html',
        employee=employee,
        employees=employees,
        available_permissions=available_permissions
    )


@app.route('/employees/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get(employee_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()  # حذف الموظف من قاعدة البيانات أولاً

        # تسجيل العملية في السجلات
        log_action = f"حذف الموظف: {employee.name}"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم حذف الموظف بنجاح", "success")
    else:
        flash("الموظف غير موجود", "danger")
    return redirect(url_for('list_employees'))


# ================== وظائف مساعدة ==================
def save_file(file):
    if not file:
        return None

    filename = datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + secure_filename(file.filename)
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))
    return filename


# ================== عروض الإيجار وسط ==================
@app.route("/rentalm_offers/list.html")
@login_required
@permission_required('rentalm_offers_view')
def rentalm_offers():
    offers = RentalOffer.query.filter_by(district='وسط').all()
    return render_template("rentalm_offers/list.html", offers=offers, district='وسط')

def save_file(file):
    """حفظ الملف وإرجاع اسم الملف"""
    if not file:
        return None
    filename = secure_filename(file.filename)
    image_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(image_folder, exist_ok=True)
    file.save(os.path.join(image_folder, filename))
    return filename


@app.route("/rentalm_offers/add.html", methods=["GET", "POST"])
@login_required
@permission_required('rentalm_offers_add')
def add_rentalm_offer():
    if request.method == "POST":
        images_files = request.files.getlist('images')
        images_filenames = [save_file(f) for f in images_files if f and f.filename]

        new_offer = RentalOffer(
            unit_type=request.form.get("unit_type"),
            area=request.form.get("area"),
            price=float(request.form.get("price")),
            floor=request.form.get("floor"),
            detalis=request.form.get("detalis"),
            owner_type=request.form.get("owner_type"),
            location=request.form.get("location"),
            marketer=request.form.get("marketer"),
            notes=request.form.get("notes"),
            status=request.form.get("status"),
            images=images_filenames,
            district='وسط'
        )

        db.session.add(new_offer)
        db.session.commit()

        # تسجيل العملية في السجل
        log_action = f"إضافة عرض إيجار وسط: {new_offer.unit_type} - {new_offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تمت إضافة عرض الإيجار وسط بنجاح", "success")
        return redirect(url_for("rentalm_offers"))

    return render_template("rentalm_offers/add.html", district='وسط')



@app.route('/rentalm_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalm_offers_edit')
def edit_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    if request.method == "POST":
        # تحديث بيانات العرض
        offer.unit_type = request.form.get("unit_type")
        offer.area = request.form.get("area")
        offer.floor = request.form.get("floor")
        offer.price = float(request.form.get("price"))
        offer.detalis = request.form.get("detalis")
        offer.owner_type = request.form.get("owner_type")
        offer.location = request.form.get("location")
        offer.marketer = request.form.get("marketer")
        offer.notes = request.form.get("notes")
        offer.status = request.form.get("status")

        # التعامل مع رفع صورة جديدة
        images_files = request.files.getlist('images')
        if images_files and any(f.filename for f in images_files):
            # إزالة الصور القديمة
            for old_image in offer.images:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image))
                except:
                    pass
            offer.images = [save_file(f) for f in images_files if f.filename]

        # حفظ التعديلات في قاعدة البيانات
        db.session.commit()

        # تسجيل الإجراء في سجل العمليات
        log_action = f"تعديل عرض الإيجار وسط: {offer.unit_type} - {offer.area}م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تعديل عرض الإيجار وسط بنجاح", "success")
        return redirect(url_for("rentalm_offers"))

    return render_template("rentalm_offers/edit.html", offer=offer)


@app.route('/rentalm_offers/delete/<int:offer_id>', methods=['POST'])
@login_required
@permission_required('rentalm_offers_delete')
def delete_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)

    # حذف صورة العرض من السيرفر إذا موجودة
    for img in offer.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img))
        except:
            pass
    db.session.delete(offer)
    db.session.commit()


    # تسجيل الإجراء في سجل العمليات قبل الحذف
    log_action = f"حذف عرض الإيجار وسط: {offer.unit_type} - {offer.area}م²"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)

    # حذف العرض من قاعدة البيانات
    db.session.delete(offer)
    db.session.commit()

    flash("تم حذف عرض الإيجار وسط بنجاح", "success")
    return redirect(url_for('rentalm_offers'))



# ================== عروض الإيجار جنوب ==================
@app.route("/rentalw_offers/list.html")
@login_required
@permission_required('rentalw_offers_view')
def rentalw_offers():
    offers = RentalOffer.query.filter_by(district='جنوب').all()
    return render_template("rentalw_offers/list.html", offers=offers, district='جنوب')

def save_file(file):
    """حفظ الملف وإرجاع اسم الملف"""
    if not file:
        return None
    filename = secure_filename(file.filename)
    image_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(image_folder, exist_ok=True)
    file.save(os.path.join(image_folder, filename))
    return filename


@app.route("/rentalw_offers/add.html", methods=["GET", "POST"])
@login_required
@permission_required('rentalw_offers_add')
def add_rentalw_offer():
    if request.method == "POST":
        images_files = request.files.getlist('images')
        images_filenames = [save_file(f) for f in images_files if f and f.filename]


        new_offer = RentalOffer(
            unit_type=request.form.get("unit_type"),
            area=request.form.get("area"),
            price=float(request.form.get("price")),
            floor=request.form.get("floor"),
            detalis=request.form.get("detalis"),
            owner_type=request.form.get("owner_type"),
            location=request.form.get("location"),
            marketer=request.form.get("marketer"),
            notes=request.form.get("notes"),
            status=request.form.get("status"),
            images=images_filenames,
            district='جنوب'
        )

        # إضافة العرض إلى قاعدة البيانات
        db.session.add(new_offer)
        db.session.commit()

        # تسجيل العملية في السجل
        log_action = f"إضافة عرض إيجار جنوب: {new_offer.unit_type} - {new_offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()
        
        flash("تمت إضافة عرض الإيجار جنوب بنجاح", "success")
        return redirect(url_for("rentalw_offers"))

    return render_template("rentalw_offers/add.html", district='جنوب')


@app.route("/rentalw_offers/edit/<int:offer_id>", methods=["GET", "POST"])
@login_required
@permission_required('rentalw_offers_edit')
def edit_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    if request.method == "POST":
        offer.unit_type = request.form.get("unit_type")
        offer.area = request.form.get("area")
        offer.floor = request.form.get("floor")
        offer.price = float(request.form.get("price"))
        offer.detalis = request.form.get("detalis")
        offer.owner_type = request.form.get("owner_type")  # صححت الاسم
        offer.location = request.form.get("location")
        offer.marketer = request.form.get("marketer")
        offer.notes = request.form.get("notes")
        offer.status = request.form.get("status")

        images_files = request.files.getlist('images')
        if images_files and any(f.filename for f in images_files):
            # إزالة الصور القديمة
            for old_image in offer.images:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image))
                except:
                    pass
            offer.images = [save_file(f) for f in images_files if f.filename]


        db.session.commit()

        # تسجيل العملية في السجل
        log_action = f"تعديل عرض إيجار جنوب: {offer.unit_type} - {offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تعديل عرض الإيجار جنوب بنجاح ✅", "success")
        return redirect(url_for("rentalw_offers"))

    return render_template("rentalw_offers/edit.html", offer=offer)


@app.route('/rentalw_offers/delete/<int:offer_id>', methods=['POST'])
@login_required
@permission_required('rentalw_offers_delete')
def delete_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    
    # حفظ معلومات العرض قبل الحذف لتسجيلها
    offer_info = f"{offer.unit_type} - {offer.area} م²"

    if offer.images:
        for img in offer.images:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img))
            except:
                pass

    db.session.delete(offer)
    db.session.commit()
    
    # تسجيل العملية في السجل
    log_action = f"حذف عرض إيجار جنوب: {offer_info}"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)
    db.session.commit()
    
    flash("تم حذف عرض الإيجار جنوب بنجاح", "success")
    return redirect(url_for('rentalw_offers'))


# ================== عروض البيع وسط ==================
@app.route('/salesm_offers/list')
@login_required
@permission_required('salesm_offers_view')
def salesm_offers():
    offers = SaleOffer.query.filter_by(district='وسط').all()
    return render_template('salesm_offers/list.html', offers=offers, district="وسط")


def save_file(file):
    """حفظ الملف وإرجاع اسم الملف"""
    if not file:
        return None
    filename = secure_filename(file.filename)
    image_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(image_folder, exist_ok=True)
    file.save(os.path.join(image_folder, filename))
    return filename


@app.route("/salesm_offers/add", methods=["GET", "POST"])
@login_required
@permission_required('salesm_offers_add')
def add_salesm_offer():
    if request.method == "POST":
        images_files = request.files.getlist('images')
        images_filenames = [save_file(f) for f in images_files if f and f.filename]

        try:
            area_value = float(request.form.get("area") or 0)
            price_value = float(request.form.get("price") or 0)
            sale_limit_value = float(request.form.get("sale_limit") or 0)
        except ValueError:
            flash("السعر أو المساحة غير صالحة", "danger")
            return redirect(url_for("add_salesm_offer"))

        new_offer = SaleOffer(
            unit_type=request.form.get("unit_type"),
            area=area_value,
            floor=request.form.get("floor"),
            details=request.form.get("details"),
            price=price_value,
            sale_limit=sale_limit_value,
            front=request.form.get("front"),
            street=request.form.get("street"),
            location=request.form.get("location"),
            marketer=request.form.get("marketer"),
            owner_type=request.form.get("owner_type"),
            notes=request.form.get("notes"),
            status=request.form.get("status"),
            images=images_filenames,
            district="وسط",
            created_by=current_user.username
        )

        db.session.add(new_offer)
        db.session.commit()

        log_action = f"إضافة عرض بيع وسط: {new_offer.unit_type} - {new_offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تمت إضافة عرض البيع وسط بنجاح ✅", "success")
        return redirect(url_for("salesm_offers"))

    return render_template("salesm_offers/add.html")


@app.route('/edit_salesm_offer/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('salesm_offers_edit')
def edit_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    if request.method == "POST":
        try:
            offer.area = float(request.form.get("area") or 0)
            offer.price = float(request.form.get("price") or 0)
            offer.sale_limit = float(request.form.get("sale_limit") or 0)
        except ValueError:
            flash("السعر أو المساحة غير صالحة", "danger")
            return redirect(url_for("edit_salesm_offer", offer_id=offer_id))

        offer.unit_type  = request.form.get("unit_type")
        offer.floor      = request.form.get("floor")
        offer.details    = request.form.get("details")
        offer.front      = request.form.get("front")
        offer.street     = request.form.get("street")
        offer.owner_type = request.form.get("owner_type")
        offer.location   = request.form.get("location")
        offer.marketer   = request.form.get("marketer")
        offer.notes      = request.form.get("notes")
        offer.status     = request.form.get("status")
        offer.district   = request.form.get("district")

        images_files = request.files.getlist('images')
        if images_files and any(f.filename for f in images_files):
            # إزالة الصور القديمة
            for old_image in offer.images:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image))
                except:
                    pass
            offer.images = [save_file(f) for f in images_files if f.filename]

        db.session.commit()

        log_action = f"تعديل عرض بيع وسط: {offer.unit_type} - {offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تعديل عرض البيع وسط بنجاح ✅", "success")
        return redirect(url_for("salesm_offers"))

    return render_template("salesm_offers/edit.html", offer=offer)


@app.route('/salesm_offers/delete/<int:offer_id>', methods=['POST'])
@login_required
@permission_required('salesm_offers_delete')
def delete_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    # إزالة الصور
    for img in offer.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img))
        except:
            pass
    db.session.delete(offer)
    db.session.commit()

    log_action = f"حذف عرض بيع وسط: {offer.unit_type} - {offer.area} م²"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)
    db.session.commit()

    flash("تم حذف عرض البيع وسط بنجاح ✅", "success")
    return redirect(url_for('salesm_offers'))


# ================== عروض البيع جنوب ==================
@app.route('/salesw_offers/list')
@login_required
@permission_required('salesw_offers_view')
def salesw_offers():
    offers = SaleOffer.query.filter_by(district='جنوب').all()
    return render_template('salesw_offers/list.html', offers=offers, district='جنوب')


@app.route('/salesw_offers/add', methods=['GET', 'POST'])
@login_required
@permission_required('salesw_offers_add')
def add_salesw_offer():
    if request.method == "POST":
        images_files = request.files.getlist('images')
        images_filenames = [save_file(f) for f in images_files if f and f.filename]

        try:
            area_value = float(request.form.get("area") or 0)
            price_value = float(request.form.get("price") or 0)
            sale_limit_value = float(request.form.get("sale_limit") or 0)
        except ValueError:
            flash("السعر أو المساحة غير صالحة", "danger")
            return redirect(url_for("add_salesw_offer"))

        new_offer = SaleOffer(
            unit_type=request.form.get("unit_type"),
            area=area_value,
            floor=request.form.get("floor"),
            details=request.form.get("details"),
            price=price_value,
            sale_limit=sale_limit_value,
            front=request.form.get("front"),
            street=request.form.get("street"),
            location=request.form.get("location"),
            marketer=request.form.get("marketer"),
            owner_type=request.form.get("owner_type"),
            notes=request.form.get("notes"),
            status=request.form.get("status"),
            images=images_filenames,
            district="جنوب",
            created_by=current_user.username
        )

        db.session.add(new_offer)
        db.session.commit()

        log_action = f"إضافة عرض بيع جنوب: {new_offer.unit_type} - {new_offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تمت إضافة عرض البيع جنوب بنجاح ✅", "success")
        return redirect(url_for("salesw_offers"))

    return render_template("salesw_offers/add.html")


@app.route('/edit_salesw_offer/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('salesw_offers_edit')
def edit_salesw_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    if request.method == "POST":
        try:
            offer.area = float(request.form.get("area") or 0)
            offer.price = float(request.form.get("price") or 0)
            offer.sale_limit = float(request.form.get("sale_limit") or 0)
        except ValueError:
            flash("السعر أو المساحة غير صالحة", "danger")
            return redirect(url_for("edit_salesw_offer", offer_id=offer_id))

        offer.unit_type  = request.form.get("unit_type")
        offer.floor      = request.form.get("floor")
        offer.details    = request.form.get("details")
        offer.front      = request.form.get("front")
        offer.street     = request.form.get("street")
        offer.owner_type = request.form.get("owner_type")
        offer.location   = request.form.get("location")
        offer.marketer   = request.form.get("marketer")
        offer.notes      = request.form.get("notes")
        offer.status     = request.form.get("status")
        offer.district   = request.form.get("district")

        images_files = request.files.getlist('images')
        if images_files and any(f.filename for f in images_files):
            # إزالة الصور القديمة
            for old_image in offer.images:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image))
                except:
                    pass
            offer.images = [save_file(f) for f in images_files if f.filename]

        db.session.commit()

        log_action = f"تعديل عرض بيع جنوب: {offer.unit_type} - {offer.area} م²"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تعديل عرض البيع جنوب بنجاح ✅", "success")
        return redirect(url_for("salesw_offers"))

    return render_template("salesw_offers/edit.html", offer=offer)


@app.route('/salesw_offers/delete/<int:offer_id>', methods=['POST'])
@login_required
@permission_required('salesw_offers_delete')
def delete_salesw_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    for img in offer.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img))
        except:
            pass
    db.session.delete(offer)
    db.session.commit()

    log_action = f"حذف عرض بيع جنوب: {offer.unit_type} - {offer.area} م²"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)
    db.session.commit()

    flash("تم حذف عرض البيع جنوب بنجاح ✅", "success")
    return redirect(url_for('salesw_offers'))

# ================== السجلات ==================
@app.route('/view_logs')
@login_required
@permission_required('logs')
def view_logs():
    if 'logs' not in current_user.get_permissions():  # تحقق من الصلاحية
        flash("ليس لديك صلاحية عرض السجلات", "danger")
        return redirect(url_for('dashboard'))

    # تطبيق الفلاتر
    query = Log.query
    user_filter = request.args.get('user')
    action_filter = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if user_filter:
        query = query.filter(Log.user.ilike(f"%{user_filter}%"))
    if action_filter:
        query = query.filter(Log.action.ilike(f"%{action_filter}%"))
    if date_from:
        query = query.filter(Log.timestamp >= date_from)
    if date_to:
        query = query.filter(Log.timestamp <= date_to)

    logs = query.order_by(Log.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)



# ================== الطلبات ==================

@app.route("/orders")
@login_required
@permission_required('orders_view')
def orders():
    orders_data = Orders.query.all()
    return render_template("orders.html", requests=orders_data)


@app.route("/add_request", methods=["POST"])
@login_required
@permission_required('orders_add')
def add_request():
    customer_name = request.form.get("customer_name")
    property_type = request.form.get("unit_type")
    area = request.form.get("area")
    price = request.form.get("price")
    location = request.form.get("location")
    phone = request.form.get("phone")
    marketer = request.form.get("marketer")
    notes = request.form.get("notes")

    # التحقق من الحقول المطلوبة
    if not customer_name or not property_type:
        flash("الرجاء تعبئة الحقول المطلوبة (الاسم ونوع العقار)", "danger")
        return redirect(url_for("orders"))

    # تحويل القيم الرقمية
    try:
        area_value = int(area) if area else None
        price_value = float(price) if price else None
    except ValueError:
        flash("المساحة أو السعر غير صالح", "danger")
        return redirect(url_for("orders"))

    # إضافة الطلب
    new_request = Orders(
        customer_name=customer_name,
        unit_type=property_type,
        area=area_value,
        price=price_value,
        location=location,
        phone=phone,
        marketer=marketer,
        notes=notes
    )

    db.session.add(new_request)
    db.session.commit()

    # تسجيل العملية
    log_action = f"إضافة طلب: {customer_name} - {property_type}"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)
    db.session.commit()

    flash("تم إضافة الطلب بنجاح ✅", "success")
    return redirect(url_for("orders"))


@app.route("/orders/edit/<int:id>", methods=["GET", "POST"])
@login_required
@permission_required('orders_edit')
def edit_request(id):
    req = Orders.query.get_or_404(id)
    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        property_type = request.form.get("unit_type")
        area = request.form.get("area")
        price = request.form.get("price")
        location = request.form.get("location")
        phone = request.form.get("phone")
        marketer = request.form.get("marketer")
        notes = request.form.get("notes")

        # التحقق من الحقول المطلوبة
        if not customer_name or not property_type:
            flash("الرجاء تعبئة الحقول المطلوبة (الاسم ونوع العقار)", "danger")
            return redirect(request.url)

        # تحويل القيم الرقمية
        try:
            area_value = int(area) if area else None
            price_value = float(price) if price else None
        except ValueError:
            flash("المساحة أو السعر غير صالح", "danger")
            return redirect(request.url)

        # تحديث البيانات
        req.customer_name = customer_name
        req.unit_type = property_type
        req.area = area_value
        req.price = price_value
        req.location = location
        req.phone = phone
        req.marketer = marketer
        req.notes = notes

        db.session.commit()

        # تسجيل العملية
        log_action = f"تعديل طلب: {req.customer_name} - {req.unit_type}"
        log = Log(user=current_user.username, action=log_action)
        db.session.add(log)
        db.session.commit()

        flash("تم تعديل الطلب بنجاح ✅", "success")
        return redirect(url_for("orders"))

    return render_template("edit_request.html", request=req)


@app.route("/orders/delete/<int:id>", methods=["POST"])
@login_required
@permission_required('orders_delete')
def delete_request(id):
    req = Orders.query.get_or_404(id)

    # تسجيل العملية قبل الحذف
    log_action = f"حذف طلب: {req.customer_name} - {req.unit_type}"
    log = Log(user=current_user.username, action=log_action)
    db.session.add(log)
    db.session.commit()

    # حذف الطلب
    db.session.delete(req)
    db.session.commit()

    flash("تم حذف الطلب بنجاح ✅", "success")
    return redirect(url_for("orders"))
# ================== تشغيل التطبيق ==================


from config import Config

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # إنشاء أول مستخدم إذا لم يكن موجوداً
        if Employee.query.count() == 0:
            from werkzeug.security import generate_password_hash
            admin = Employee(
                name="Admin",
                role="Administrator",
                username="admin",
                password=generate_password_hash("admin123")
            )
            admin.set_permissions([
                "logs",
                "list_employees",
                "add_employee",
                "edit_employee",
                "delete_employee",
                "rentalm_offers_view",
                "rentalm_offers_add",
                "rentalm_offers_edit",
                "rentalm_offers_delete",
                "rentalw_offers_view",
                "rentalw_offers_add",
                "rentalw_offers_edit",
                "rentalw_offers_delete",
                "salesm_offers_view",
                "salesm_offers_add",
                "salesm_offers_edit",
                "salesm_offers_delete",
                "salesw_offers_view",
                "salesw_offers_add",
                "salesw_offers_edit",
                "salesw_offers_delete",
                "orders_view",
                "orders_add",
                "orders_delete"
            ])
            db.session.add(admin)
            db.session.commit()
            print("تم إنشاء المستخدم الأول: admin / admin123")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=Config.PORT)

