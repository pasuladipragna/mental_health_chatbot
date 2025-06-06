"""Add mood_score to ChatLog

Revision ID: 566b79e3eccb
Revises: 8370f5fb4111
Create Date: 2025-05-28 19:40:57.280952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '566b79e3eccb'
down_revision = '8370f5fb4111'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mood_score', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_logs', schema=None) as batch_op:
        batch_op.drop_column('mood_score')

    # ### end Alembic commands ###
