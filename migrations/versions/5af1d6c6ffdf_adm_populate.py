"""adm populate

Revision ID: 5af1d6c6ffdf
Revises: 
Create Date: 2020-06-30 14:53:02.782245

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = '5af1d6c6ffdf'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    users_table = op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(150), unique=True, nullable=False),
        sa.Column('username', sa.String(150), nullable=False),
        sa.Column('password', sa.String(150), nullable=False),
        sa.Column('admin', sa.Boolean, nullable=False, default=False),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('removed_at', sa.DateTime(timezone=True)),
        sa.Column('removed', sa.Boolean(), nullable=False, default=False),
        mysql_charset= 'utf8mb4',
    )

    op.bulk_insert(
        users_table, 
        [
            {
                'id': str(uuid.uuid4()),
                'name': 'Scis',
                'username': 'admin',
                # qpalzm
                'password': '1c358e3d51968ace657b0f01d5eea55b7930ff3f45f75f1f9858ed1b8f9d0f83',
                'admin': True,
                'active': True,
                'created_at': datetime.utcnow(),
                'updated_at': None,
                'removed_at': None,
                'removed': False,
            }
        ]
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('valid', sa.Boolean, nullable=False, default=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        mysql_charset= 'utf8mb4',
    )

    op.create_table(
        'access_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('valid', sa.Boolean, nullable=False, default=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('refresh_token_id', sa.String(36), sa.ForeignKey('refresh_tokens.id'), nullable=False),
        mysql_charset= 'utf8mb4',
    )


def downgrade():
    op.drop_table('access_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
