"""empty message

Revision ID: 0a4979bc296c
Revises: 530d2211fc14
Create Date: 2018-08-18 20:47:43.129487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a4979bc296c'
down_revision = '530d2211fc14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Assignments', sa.Column('Due_Date', sa.DateTime(), nullable=True))
    op.add_column('Disciplines', sa.Column('CodCurso', sa.Integer(), nullable=True))
    op.add_column('Disciplines', sa.Column('IdCurso', sa.Integer(), nullable=True))
    op.add_column('Disciplines', sa.Column('Nome', sa.String(length=60), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Disciplines', 'Nome')
    op.drop_column('Disciplines', 'IdCurso')
    op.drop_column('Disciplines', 'CodCurso')
    op.drop_column('Assignments', 'Due_Date')
    # ### end Alembic commands ###
