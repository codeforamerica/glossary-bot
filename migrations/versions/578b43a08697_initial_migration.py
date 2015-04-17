"""initial migration

Revision ID: 578b43a08697
Revises: None
Create Date: 2015-04-16 17:09:52.127430

"""

# revision identifiers, used by Alembic.
revision = '578b43a08697'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('interactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('creation_date', sa.DateTime(), nullable=True),
                    sa.Column('user', sa.Unicode(), nullable=True),
                    sa.Column('term', sa.Unicode(), nullable=True),
                    sa.Column('action', sa.Unicode(), nullable=True),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_interactions_action'), 'interactions', ['action'], unique=False)

    op.create_table('definitions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('creation_date', sa.DateTime(), nullable=True),
                    sa.Column('term', sa.Unicode(), nullable=True),
                    sa.Column('definition', sa.Unicode(), nullable=True),
                    sa.Column('user', sa.Unicode(), nullable=True),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_definitions_term'), 'definitions', ['term'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_definitions_term'), table_name='definitions')
    op.drop_table('definitions')
    op.drop_index(op.f('ix_interactions_action'), table_name='interactions')
    op.drop_table('interactions')
