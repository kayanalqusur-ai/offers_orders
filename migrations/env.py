import sys
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, MetaData
from alembic import context

# إضافة جذر المشروع إلى sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Logging
config = context.config
fileConfig(config.config_file_name)

# قاعدة البيانات
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://offers_orders:qkiEgdvonowQqG5psQD4Rik2QvDdV4SA@dpg-d2t7pimuk2gs73cjkkdg-a.oregon-postgres.render.com/offers_orders"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# استيراد النماذج
from models import Employee, Log, Property, RentalOffer, SaleOffer, RentalMOffer, RentalWOffer, Orders

# Metadata لجميع الجداول
target_metadata = MetaData()
for cls in [Employee, Log, Property, RentalOffer, SaleOffer, RentalMOffer, RentalWOffer, Orders]:
    target_metadata._add_table(cls.__table__.name, cls.__table__.schema, cls.__table__)

# Offline
def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

# Online
def run_migrations_online():
    connectable = create_engine(DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
