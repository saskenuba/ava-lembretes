"""empty message

Revision ID: f9bf16f16e95
Revises: 20c264573b90
Create Date: 2018-08-19 18:14:17.489943

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9bf16f16e95'
down_revision = '20c264573b90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users_Assignments', sa.Column('UserCompleted', sa.Boolean(), nullable=True))
    op.drop_column('Users_Assignments', 'userCompleted')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users_Assignments', sa.Column('userCompleted', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Users_Assignments', 'UserCompleted')
    # ### end Alembic commands ###