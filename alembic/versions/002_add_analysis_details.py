"""add analysis details for admin panel

Revision ID: 002
Revises: 001
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001_init'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to analyses table for detailed admin view
    op.add_column('analyses', sa.Column('upload_timestamp', sa.DateTime(), nullable=True))
    op.add_column('analyses', sa.Column('analysis_duration_ms', sa.Integer(), nullable=True))
    op.add_column('analyses', sa.Column('ocr_text_preview', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('entities_json', sa.JSON(), nullable=True))
    op.add_column('analyses', sa.Column('confidence_score', sa.Float(), nullable=True))
    
    # Create index for faster admin queries
    op.create_index('ix_analyses_upload_timestamp', 'analyses', ['upload_timestamp'])

def downgrade():
    op.drop_index('ix_analyses_upload_timestamp', table_name='analyses')
    op.drop_column('analyses', 'confidence_score')
    op.drop_column('analyses', 'entities_json')
    op.drop_column('analyses', 'ocr_text_preview')
    op.drop_column('analyses', 'analysis_duration_ms')
    op.drop_column('analyses', 'upload_timestamp')
