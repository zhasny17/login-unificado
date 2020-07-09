"""alterando modelo de usuario para adicionar campo para url de imagem

Revision ID: e794f55cc5a6
Revises: 5af1d6c6ffdf
Create Date: 2020-07-09 11:17:44.528964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e794f55cc5a6'
down_revision = '5af1d6c6ffdf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('photo_url', sa.String(length=150), nullable=True))
    op.drop_index('name', table_name='users')
    op.create_unique_constraint(None, 'users', ['username'])


def downgrade():
    op.drop_constraint(None, 'users', type_='unique')
    op.create_index('name', 'users', ['name'], unique=True)
    op.drop_column('users', 'photo_url')
