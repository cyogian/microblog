"""empty message

Revision ID: dbbc0d99f48d
Revises: 3b932b3840b3
Create Date: 2020-05-01 00:24:34.237665

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbbc0d99f48d'
down_revision = '3b932b3840b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('temp_email_change',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('otp', sa.Integer(), nullable=True),
    sa.Column('userId', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('temp_email_change')
    # ### end Alembic commands ###