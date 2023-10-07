"""Description

Revision ID: 711c4b94793f
Revises: b3bf67371096
Create Date: 2023-10-03 12:14:43.318496

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '711c4b94793f'
down_revision = 'b3bf67371096'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=200), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('description')

    # ### end Alembic commands ###
