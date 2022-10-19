"""add column

Revision ID: b16b862aca47
Revises: 5fb5c7e41f72
Create Date: 2022-10-14 01:59:14.721575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b16b862aca47'
down_revision = '5fb5c7e41f72'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('test', sa.Column('name2', sa.String(length=16), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('test', 'name2')
    # ### end Alembic commands ###
