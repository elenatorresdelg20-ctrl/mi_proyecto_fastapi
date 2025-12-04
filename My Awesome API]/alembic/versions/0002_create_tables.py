"""create_tables
Revision ID: 0002_create_tables
Revises: 43c3ba015ac4
Create Date: 2025-12-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '0002_create_tables'
down_revision = '43c3ba015ac4'
branch_labels = None
depends_on = None


def table_exists(conn, name):
    insp = inspect(conn)
    return name in insp.get_table_names()


def upgrade():
    conn = op.get_bind()

    if not table_exists(conn, 'tenants'):
        op.create_table(
            'tenants',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('name', sa.String, nullable=False),
            sa.Column('code', sa.String, nullable=False, unique=True),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('1'), nullable=False),
            sa.Column('logo_url', sa.String, nullable=True),
            sa.Column('primary_color', sa.String, nullable=True),
        )

    if not table_exists(conn, 'users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('username', sa.String, nullable=False, unique=True),
            sa.Column('full_name', sa.String, nullable=True),
            sa.Column('email', sa.String, nullable=True, unique=True),
            sa.Column('hashed_password', sa.String, nullable=False),
            sa.Column('tenant_id', sa.Integer, sa.ForeignKey('tenants.id'), nullable=False),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('1'), nullable=False),
            sa.Column('is_tenant_admin', sa.Boolean, server_default=sa.text('0'), nullable=False),
        )

    if not table_exists(conn, 'permissions'):
        op.create_table(
            'permissions',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('code', sa.String, nullable=False, unique=True),
            sa.Column('description', sa.String, nullable=True),
        )

    if not table_exists(conn, 'user_permissions'):
        op.create_table(
            'user_permissions',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
            sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id'), nullable=False),
            sa.UniqueConstraint('user_id', 'permission_id', name='uix_user_permission'),
        )

    if not table_exists(conn, 'sales'):
        op.create_table(
            'sales',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('tenant_id', sa.Integer, nullable=True, index=True),
            sa.Column('date', sa.DateTime, nullable=True, index=True),
            sa.Column('product', sa.String, nullable=True),
            sa.Column('amount', sa.Float, nullable=True),
            sa.Column('channel', sa.String, nullable=True, server_default='Upload'),
        )

    if not table_exists(conn, 'feedback'):
        op.create_table(
            'feedback',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('tenant_id', sa.Integer, nullable=True, index=True),
            sa.Column('date', sa.DateTime, nullable=True, index=True),
            sa.Column('text', sa.String, nullable=True),
            sa.Column('sentiment_label', sa.String, nullable=True),
            sa.Column('sentiment_score', sa.Float, nullable=True),
            sa.Column('is_corrected', sa.Boolean, server_default=sa.text('0'), nullable=False),
        )

    if not table_exists(conn, 'external_integrations'):
        op.create_table(
            'external_integrations',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('tenant_id', sa.Integer, nullable=True, index=True),
            sa.Column('provider', sa.String, nullable=True, index=True),
            sa.Column('name', sa.String, nullable=False),
            sa.Column('auth_type', sa.String, nullable=False),
            sa.Column('api_key', sa.String, nullable=True),
            sa.Column('access_token', sa.String, nullable=True),
            sa.Column('refresh_token', sa.String, nullable=True),
            sa.Column('token_expires_at', sa.DateTime, nullable=True),
            sa.Column('extra_config', sa.String, nullable=True),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('1'), nullable=False),
            sa.Column('created_at', sa.DateTime, nullable=True),
            sa.Column('updated_at', sa.DateTime, nullable=True),
        )


def downgrade():
    conn = op.get_bind()
    if table_exists(conn, 'external_integrations'):
        op.drop_table('external_integrations')
    if table_exists(conn, 'feedback'):
        op.drop_table('feedback')
    if table_exists(conn, 'sales'):
        op.drop_table('sales')
    if table_exists(conn, 'user_permissions'):
        op.drop_table('user_permissions')
    if table_exists(conn, 'permissions'):
        op.drop_table('permissions')
    if table_exists(conn, 'users'):
        op.drop_table('users')
    if table_exists(conn, 'tenants'):
        op.drop_table('tenants')
