"""initial setup

Revision ID: 79eb33f11b7a
Revises: 97cc7d137625
Create Date: 2025-09-07 17:09:55.073228

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '79eb33f11b7a'
down_revision = '97cc7d137625'
branch_labels = None
depends_on = None


def upgrade():
    # تحويل images من BYTEA إلى VARCHAR[] (مع كاست واضح)
    op.execute("""
        ALTER TABLE property
        ALTER COLUMN images
        TYPE VARCHAR[]
        USING ARRAY[images::text];
    """)

    with op.batch_alter_table('rental_m_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('images', postgresql.ARRAY(sa.String()), nullable=True))
        batch_op.drop_column('image4')
        batch_op.drop_column('image1')
        batch_op.drop_column('image3')
        batch_op.drop_column('image2')
        batch_op.drop_column('detalis')
        batch_op.drop_column('image5')

    with op.batch_alter_table('rental_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('details', sa.String(length=50), nullable=True))
        batch_op.drop_column('detalis')

    with op.batch_alter_table('rental_w_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('images', postgresql.ARRAY(sa.String()), nullable=True))
        batch_op.drop_column('image4')
        batch_op.drop_column('image1')
        batch_op.drop_column('image3')
        batch_op.drop_column('image2')
        batch_op.drop_column('detalis')
        batch_op.drop_column('image5')

    with op.batch_alter_table('sale_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.drop_column('detalis')


def downgrade():
    with op.batch_alter_table('sale_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('detalis', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_column('updated_at')
        batch_op.drop_column('details')

    with op.batch_alter_table('rental_w_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image5', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('detalis', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image2', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image3', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image1', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image4', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.drop_column('images')
        batch_op.drop_column('details')

    with op.batch_alter_table('rental_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('detalis', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
        batch_op.drop_column('details')

    with op.batch_alter_table('rental_m_offer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image5', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('detalis', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image2', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image3', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image1', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('image4', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.drop_column('images')
        batch_op.drop_column('details')

    with op.batch_alter_table('property', schema=None) as batch_op:
        batch_op.alter_column(
            'images',
            existing_type=postgresql.ARRAY(sa.String()),
            type_=postgresql.BYTEA(),
            existing_nullable=True,
            postgresql_using="decode(images[1], 'escape')"
        )
