"""Encrypt external_integrations.api_key and access_token using FERNET_KEY

Revision ID: 0003_encrypt_external_integrations
Revises: 0002_create_tables
Create Date: 2025-12-03 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import sys
import logging

# revision identifiers, used by Alembic.
revision = '0003_encrypt_external_integrations'
down_revision = '0002_create_tables'
branch_labels = None
depends_on = None


def get_fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception:
        return None
    key = os.environ.get('FERNET_KEY')
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def upgrade():
    """Idempotent data migration: encrypt specified fields if not already encrypted.

    IMPORTANT: This migration requires `FERNET_KEY` env var set when run.
    It will skip if the table does not exist.
    """
    bind = op.get_bind()
    session = Session(bind=bind)

    f = get_fernet()
    if not f:
        raise RuntimeError('FERNET_KEY not set or cryptography not available. Set FERNET_KEY to apply this migration.')

    # Check table exists
    inspector = sa.inspect(bind)
    if 'external_integrations' not in inspector.get_table_names():
        # nothing to do
        return

    logger = logging.getLogger('alembic.encrypt_external_integrations')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    try:
        rows = session.execute(text('select id, api_key, access_token from external_integrations')).fetchall()
        updated = 0
        processed = 0
        for r in rows:
            id_, api_key, access_token = r
            processed += 1
            new_api = None
            new_token = None
            if api_key and not (isinstance(api_key, str) and api_key.startswith('enc:')):
                new_api = 'enc:' + f.encrypt(str(api_key).encode()).decode()
            if access_token and not (isinstance(access_token, str) and access_token.startswith('enc:')):
                new_token = 'enc:' + f.encrypt(str(access_token).encode()).decode()
            if new_api is not None or new_token is not None:
                stmt = []
                params = {'id': id_}
                if new_api is not None:
                    stmt.append('api_key = :api_key')
                    params['api_key'] = new_api
                if new_token is not None:
                    stmt.append('access_token = :access_token')
                    params['access_token'] = new_token
                sql = 'update external_integrations set {} where id = :id'.format(', '.join(stmt))
                session.execute(text(sql), params)
                updated += 1
        if updated > 0:
            session.commit()
        logger.info('Processed %d rows, updated %d rows (encrypted fields).', processed, updated)
    except Exception as exc:
        session.rollback()
        logger.exception('Error durante migration de cifrado: %s', exc)
        raise
    finally:
        session.close()


def downgrade():
    # Downgrade not supported for this data migration (can't decrypt without key history).
    pass
