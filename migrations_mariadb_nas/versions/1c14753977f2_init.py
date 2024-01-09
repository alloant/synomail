"""Init

Revision ID: 1c14753977f2
Revises: 4bd4aeca95e2
Create Date: 2024-01-06 12:13:14.660415

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1c14753977f2'
down_revision = '4bd4aeca95e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note', schema=None) as batch_op:
        batch_op.alter_column('proc',
               existing_type=mysql.VARCHAR(length=15),
               type_=sa.String(length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note', schema=None) as batch_op:
        batch_op.alter_column('proc',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=15),
               existing_nullable=False)

    # ### end Alembic commands ###