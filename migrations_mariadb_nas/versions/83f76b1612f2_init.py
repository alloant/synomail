"""Init

Revision ID: 83f76b1612f2
Revises: 
Create Date: 2024-01-06 11:29:40.992601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83f76b1612f2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('password', sa.String(length=100), nullable=False),
    sa.Column('password_nas', sa.String(length=100), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('alias', sa.String(length=20), nullable=False),
    sa.Column('u_groups', sa.String(length=200), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('local_path', sa.String(length=200), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('admin_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('alias')
    )
    op.create_table('note',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('n_date', sa.Date(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('proc', sa.String(length=15), nullable=False),
    sa.Column('path', sa.String(length=150), nullable=False),
    sa.Column('permanent_link', sa.String(length=150), nullable=False),
    sa.Column('comments', sa.Text(), nullable=False),
    sa.Column('permanent', sa.Boolean(), nullable=False),
    sa.Column('reg', sa.String(length=15), nullable=False),
    sa.Column('n_groups', sa.String(length=15), nullable=False),
    sa.Column('done', sa.Boolean(), nullable=False),
    sa.Column('state', sa.Integer(), nullable=False),
    sa.Column('received_by', sa.String(length=150), nullable=False),
    sa.Column('read_by', sa.String(length=150), nullable=False),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('subject', sa.String(length=150), nullable=False),
    sa.Column('path', sa.String(length=150), nullable=False),
    sa.Column('permanent_link', sa.String(length=150), nullable=False),
    sa.Column('sender', sa.String(length=20), nullable=False),
    sa.Column('note_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['note_id'], ['note.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('note_receiver',
    sa.Column('note_id', sa.Integer(), nullable=True),
    sa.Column('receiver_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['note_id'], ['note.id'], ),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], )
    )
    op.create_table('note_ref',
    sa.Column('note_id', sa.Integer(), nullable=True),
    sa.Column('ref_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['note_id'], ['note.id'], ),
    sa.ForeignKeyConstraint(['ref_id'], ['note.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('note_ref')
    op.drop_table('note_receiver')
    op.drop_table('file')
    op.drop_table('note')
    op.drop_table('user')
    # ### end Alembic commands ###
