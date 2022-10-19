"""add column

Revision ID: c124c37d37e7
Revises: 881889e81d42
Create Date: 2022-10-14 02:26:30.609612

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c124c37d37e7'
down_revision = '881889e81d42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('test2', 'name4')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('test2', sa.Column('name4', mysql.VARCHAR(length=16), nullable=False))
    # ### end Alembic commands ###
