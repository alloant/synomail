"""Init

Revision ID: 4bd4aeca95e2
Revises: 83f76b1612f2
Create Date: 2024-01-06 11:32:35.373239

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4bd4aeca95e2'
down_revision = '83f76b1612f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=500),
               existing_nullable=False)
        batch_op.alter_column('password_nas',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=500),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_nas',
               existing_type=sa.String(length=500),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.alter_column('password',
               existing_type=sa.String(length=500),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=False)

    # ### end Alembic commands ###
