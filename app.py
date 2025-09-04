import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from sqlalchemy import func

# ================== إعداد التطبيق ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", "your_secret_key_here")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

# ================== ملفات وصلاحيات ==================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if not file or not file.filename:
        return None
    filename = datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + secure_filename(file.filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename

def remove_files(files_list):
    if not files_list:
        return
    for f in files_list:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
        except:
            pass

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

# ================== النماذج ==================
class Employee(db.Model, UserMixin):
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

# ================== المستخدم ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Employee.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"مرحباً {user.username}", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("اسم المستخدم أو كلمة المرور خاطئة", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج بنجاح ✅", "success")
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
        return f"حدث خطأ في dashboard: {e}", 500

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
@permission_required('list_employees')
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

@app.route('/employees/edit/<int:employee_id>')
@login_required
@permission_required('edit_employee')
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
    return render_template('employees/edit.html', employees=employees, available_permissions=available_permissions, employee=employee)

@app.route('/employees/delete/<int:employee_id>')
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
    
    # تسجيل العملية في السجلات
    log = Log(user=current_user.username, action=f"حذف الموظف: {name}")
    db.session.add(log)
    db.session.commit()
    
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
                filename = save_file(file)
                if filename:
                    images.append(filename)

        offer = RentalOffer(
            unit_type=request.form['unit_type'],
            floor=request.form['floor'],
            area=float(request.form['area']) if request.form['area'] else None,
            price=float(request.form['price']) if request.form['price'] else None,
            detalis=request.form['detalis'],
            owner_type=request.form['owner_type'],
            location=request.form['location'],
            marketer=request.form['marketer'],
            notes=request.form['notes'],
            status=request.form['status'],
            district='وسط',
            images=images
        )
        
        db.session.add(offer)
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"إضافة عرض إيجار وسط: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('rentalm_offers'))
    
    return render_template('rental_offers/add.html', district='وسط', district_name='وسط')

@app.route('/rentalm_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalm_offers_edit')
def edit_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    
    if request.method == 'POST':
        # حفظ الصور الجديدة
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                filename = save_file(file)
                if filename:
                    new_images.append(filename)
        
        # إذا تم رفع صور جديدة، احذف القديمة
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images
        
        offer.unit_type = request.form['unit_type']
        offer.floor = request.form['floor']
        offer.area = float(request.form['area']) if request.form['area'] else None
        offer.price = float(request.form['price']) if request.form['price'] else None
        offer.detalis = request.form['detalis']
        offer.owner_type = request.form['owner_type']
        offer.location = request.form['location']
        offer.marketer = request.form['marketer']
        offer.notes = request.form['notes']
        offer.status = request.form['status']
        offer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"تعديل عرض إيجار وسط: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('rentalm_offers'))
    
    return render_template('rental_offers/add.html', offer=offer, district='وسط', district_name='وسط')

@app.route('/rentalm_offers/delete/<int:offer_id>')
@login_required
@permission_required('rentalm_offers_delete')
def delete_rentalm_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    
    # حذف الصور المرفقة
    remove_files(offer.images or [])
    
    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()
    
    # تسجيل العملية في السجلات
    log = Log(user=current_user.username, action=f"حذف عرض إيجار وسط: {unit_type}")
    db.session.add(log)
    db.session.commit()
    
    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('rentalm_offers'))

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
                filename = save_file(file)
                if filename:
                    images.append(filename)

        offer = RentalOffer(
            unit_type=request.form['unit_type'],
            floor=request.form['floor'],
            area=float(request.form['area']) if request.form['area'] else None,
            price=float(request.form['price']) if request.form['price'] else None,
            detalis=request.form['detalis'],
            owner_type=request.form['owner_type'],
            location=request.form['location'],
            marketer=request.form['marketer'],
            notes=request.form['notes'],
            status=request.form['status'],
            district='جنوب',
            images=images
        )
        
        db.session.add(offer)
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"إضافة عرض إيجار جنوب: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('rentalw_offers'))
    
    return render_template('rental_offers/add.html', district='جنوب', district_name='جنوب')

@app.route('/rentalw_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('rentalw_offers_edit')
def edit_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    
    if request.method == 'POST':
        # حفظ الصور الجديدة
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                filename = save_file(file)
                if filename:
                    new_images.append(filename)
        
        # إذا تم رفع صور جديدة، احذف القديمة
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images
        
        offer.unit_type = request.form['unit_type']
        offer.floor = request.form['floor']
        offer.area = float(request.form['area']) if request.form['area'] else None
        offer.price = float(request.form['price']) if request.form['price'] else None
        offer.detalis = request.form['detalis']
        offer.owner_type = request.form['owner_type']
        offer.location = request.form['location']
        offer.marketer = request.form['marketer']
        offer.notes = request.form['notes']
        offer.status = request.form['status']
        offer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"تعديل عرض إيجار جنوب: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('rentalw_offers'))
    
    return render_template('rental_offers/add.html', offer=offer, district='جنوب', district_name='جنوب')

@app.route('/rentalw_offers/delete/<int:offer_id>')
@login_required
@permission_required('rentalw_offers_delete')
def delete_rentalw_offer(offer_id):
    offer = RentalOffer.query.get_or_404(offer_id)
    
    # حذف الصور المرفقة
    remove_files(offer.images or [])
    
    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()
    
    # تسجيل العملية في السجلات
    log = Log(user=current_user.username, action=f"حذف عرض إيجار جنوب: {unit_type}")
    db.session.add(log)
    db.session.commit()
    
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
                filename = save_file(file)
                if filename:
                    images.append(filename)

        offer = SaleOffer(
            unit_type=request.form['unit_type'],
            district='وسط',
            area=float(request.form['area']) if request.form['area'] else None,
            floor=request.form['floor'],
            front=request.form['front'],
            street=request.form['street'],
            price=float(request.form['price']) if request.form['price'] else None,
            sale_limit=float(request.form['sale_limit']) if request.form['sale_limit'] else None,
            location=request.form['location'],
            detalis=request.form['detalis'],
            marketer=request.form['marketer'],
            owner_type=request.form['owner_type'],
            status=request.form['status'],
            images=images,
            notes=request.form['notes'],
            created_by=current_user.username
        )
        
        db.session.add(offer)
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"إضافة عرض بيع وسط: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تمت إضافة العرض بنجاح ✅", "success")
        return redirect(url_for('salesm_offers'))
    
    return render_template('sale_offers/add.html', district='وسط', district_name='وسط')

@app.route('/salesm_offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
@permission_required('salesm_offers_edit')
def edit_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    
    if request.method == 'POST':
        # حفظ الصور الجديدة
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                filename = save_file(file)
                if filename:
                    new_images.append(filename)
        
        # إذا تم رفع صور جديدة، احذف القديمة
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images
        
        offer.unit_type = request.form['unit_type']
        offer.area = float(request.form['area']) if request.form['area'] else None
        offer.floor = request.form['floor']
        offer.front = request.form['front']
        offer.street = request.form['street']
        offer.price = float(request.form['price']) if request.form['price'] else None
        offer.sale_limit = float(request.form['sale_limit']) if request.form['sale_limit'] else None
        offer.location = request.form['location']
        offer.detalis = request.form['detalis']
        offer.marketer = request.form['marketer']
        offer.owner_type = request.form['owner_type']
        offer.status = request.form['status']
        offer.notes = request.form['notes']
        
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"تعديل عرض بيع وسط: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('salesm_offers'))
    
    return render_template('sale_offers/add.html', offer=offer, district='وسط', district_name='وسط')

@app.route('/salesm_offers/delete/<int:offer_id>')
@login_required
@permission_required('salesm_offers_delete')
def delete_salesm_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    
    # حذف الصور المرفقة
    remove_files(offer.images or [])
    
    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()
    
    # تسجيل العملية في السجلات
    log = Log(user=current_user.username, action=f"حذف عرض بيع وسط: {unit_type}")
    db.session.add(log)
    db.session.commit()
    
    flash("تم حذف العرض بنجاح ✅", "success")
    return redirect(url_for('salesm_offers'))

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
                filename = save_file(file)
                if filename:
                    images.append(filename)

        offer = SaleOffer(
            unit_type=request.form['unit_type'],
            district='جنوب',
            area=float(request.form['area']) if request.form['area'] else None,
            floor=request.form['floor'],
            front=request.form['front'],
            street=request.form['street'],
            price=float(request.form['price']) if request.form['price'] else None,
            sale_limit=float(request.form['sale_limit']) if request.form['sale_limit'] else None,
            location=request.form['location'],
            detalis=request.form['detalis'],
            marketer=request.form['marketer'],
            owner_type=request.form['owner_type'],
            status=request.form['status'],
            images=images,
            notes=request.form['notes'],
            created_by=current_user.username
        )
        
        db.session.add(offer)
        db.session.commit()
        
        # تسجيل العملية في السجلات
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
        # حفظ الصور الجديدة
        new_images = []
        for i in range(1, 6):
            file = request.files.get(f'image{i}')
            if file and allowed_file(file.filename):
                filename = save_file(file)
                if filename:
                    new_images.append(filename)
        
        # إذا تم رفع صور جديدة، احذف القديمة
        if new_images:
            remove_files(offer.images or [])
            offer.images = new_images
        
        offer.unit_type = request.form['unit_type']
        offer.area = float(request.form['area']) if request.form['area'] else None
        offer.floor = request.form['floor']
        offer.front = request.form['front']
        offer.street = request.form['street']
        offer.price = float(request.form['price']) if request.form['price'] else None
        offer.sale_limit = float(request.form['sale_limit']) if request.form['sale_limit'] else None
        offer.location = request.form['location']
        offer.detalis = request.form['detalis']
        offer.marketer = request.form['marketer']
        offer.owner_type = request.form['owner_type']
        offer.status = request.form['status']
        offer.notes = request.form['notes']
        
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"تعديل عرض بيع جنوب: {offer.unit_type}")
        db.session.add(log)
        db.session.commit()
        
        flash("تم تحديث العرض بنجاح ✅", "success")
        return redirect(url_for('salesw_offers'))
    
    return render_template('sale_offers/add.html', offer=offer, district='جنوب', district_name='جنوب')

@app.route('/salesw_offers/delete/<int:offer_id>')
@login_required
@permission_required('salesw_offers_delete')
def delete_salesw_offer(offer_id):
    offer = SaleOffer.query.get_or_404(offer_id)
    
    # حذف الصور المرفقة
    remove_files(offer.images or [])
    
    unit_type = offer.unit_type
    db.session.delete(offer)
    db.session.commit()
    
    # تسجيل العملية في السجلات
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
    orders_list = Orders.query.order_by(Orders.created_at.desc()).all()
    return render_template('orders/list.html', orders=orders_list)

@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
@permission_required('orders_add')
def add_order():
    if request.method == 'POST':
        order = Orders(
            customer_name=request.form['customer_name'],
            unit_type=request.form['unit_type'],
            area=int(request.form['area']) if request.form['area'] else None,
            price=float(request.form['price']) if request.form['price'] else None,
            location=request.form['location'],
            phone=request.form['phone'],
            marketer=request.form['marketer'],
            notes=request.form['notes']
        )
        
        db.session.add(order)
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"إضافة طلب جديد: {order.customer_name}")
        db.session.add(log)
        db.session.commit()
        
        flash("تمت إضافة الطلب بنجاح ✅", "success")
        return redirect(url_for('orders'))
    
    return render_template('orders/add.html')

@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
@permission_required('orders_edit')
def edit_order(order_id):
    order = Orders.query.get_or_404(order_id)
    
    if request.method == 'POST':
        order.customer_name = request.form['customer_name']
        order.unit_type = request.form['unit_type']
        order.area = int(request.form['area']) if request.form['area'] else None
        order.price = float(request.form['price']) if request.form['price'] else None
        order.location = request.form['location']
        order.phone = request.form['phone']
        order.marketer = request.form['marketer']
        order.notes = request.form['notes']
        
        db.session.commit()
        
        # تسجيل العملية في السجلات
        log = Log(user=current_user.username, action=f"تعديل الطلب: {order.customer_name}")
        db.session.add(log)
        db.session.commit()
        
        flash("تم تحديث الطلب بنجاح ✅", "success")
        return redirect(url_for('orders'))
    
    return render_template('orders/add.html', order=order)

@app.route('/orders/delete/<int:order_id>')
@login_required
@permission_required('orders_delete')
def delete_order(order_id):
    order = Orders.query.get_or_404(order_id)
    
    customer_name = order.customer_name
    db.session.delete(order)
    db.session.commit()
    
    # تسجيل العملية في السجلات
    log = Log(user=current_user.username, action=f"حذف الطلب: {customer_name}")
    db.session.add(log)
    db.session.commit()
    
    flash("تم حذف الطلب بنجاح ✅", "success")
    return redirect(url_for('orders'))

# ================== السجلات ==================
@app.route('/logs')
@login_required
@permission_required('logs')
def logs():
    logs_list = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
    return render_template('logs.html', logs=logs_list)

# ================== رفع الملفات ==================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ================== إنشاء الجداول وتشغيل التطبيق ==================
with app.app_context():
    db.create_all()
    
    # إنشاء مستخدم افتراضي إذا لم يكن موجود
    if not Employee.query.first():
        admin = Employee(
            name='المدير',
            role='مدير النظام',
            username='admin',
            password=generate_password_hash('admin123')
        )
        admin.set_permissions([
            'logs', 'list_employees', 'add_employee', 'edit_employee', 'delete_employee',
            'rentalm_offers_view', 'rentalm_offers_add', 'rentalm_offers_edit', 'rentalm_offers_delete',
            'rentalw_offers_view', 'rentalw_offers_add', 'rentalw_offers_edit', 'rentalw_offers_delete',
            'salesm_offers_view', 'salesm_offers_add', 'salesm_offers_edit', 'salesm_offers_delete',
            'salesw_offers_view', 'salesw_offers_add', 'salesw_offers_edit', 'salesw_offers_delete',
            'orders_view', 'orders_add', 'orders_edit', 'orders_delete'
        ])
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
