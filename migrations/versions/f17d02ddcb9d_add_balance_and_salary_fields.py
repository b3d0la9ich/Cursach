"""Add balance and salary fields

Revision ID: f17d02ddcb9d
Revises: 2dffc6e41369
Create Date: 2024-12-21 20:43:33.559802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f17d02ddcb9d'
down_revision = '2dffc6e41369'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('balance', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('salary_per_minute', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('salary_per_minute')
        batch_op.drop_column('balance')

    # ### end Alembic commands ###