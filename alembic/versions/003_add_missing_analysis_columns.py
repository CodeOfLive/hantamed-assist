"""add missing analysis columns for admin panel

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    """Add missing columns with IF NOT EXISTS for safety"""
    
    # PostgreSQL supports IF NOT EXISTS for ADD COLUMN (v9.6+)
    # Using op.execute for raw SQL with safety check
    
    # analysis_duration_ms
    op.execute("""
        ALTER TABLE analyses 
        ADD COLUMN IF NOT EXISTS analysis_duration_ms INTEGER
    """)
    
    # ocr_text_preview
    op.execute("""
        ALTER TABLE analyses 
        ADD COLUMN IF NOT EXISTS ocr_text_preview TEXT
    """)
    
    # entities_json (JSON type for structured data)
    op.execute("""
        ALTER TABLE analyses 
        ADD COLUMN IF NOT EXISTS entities_json JSONB
    """)
    
    # confidence_score (duplicate of avg_confidence but for explicit admin queries)
    op.execute("""
        ALTER TABLE analyses 
        ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION
    """)
    
    # Create index for faster admin panel queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analyses_upload_timestamp 
        ON analyses (upload_timestamp)
    """)

def downgrade():
    """Remove columns (careful: data loss)"""
    # Only drop if column exists (PostgreSQL 9.6+)
    op.execute("""
        ALTER TABLE analyses 
        DROP COLUMN IF EXISTS analysis_duration_ms
    """)
    op.execute("""
        ALTER TABLE analyses 
        DROP COLUMN IF EXISTS ocr_text_preview
    """)
    op.execute("""
        ALTER TABLE analyses 
        DROP COLUMN IF EXISTS entities_json
    """)
    op.execute("""
        ALTER TABLE analyses 
        DROP COLUMN IF EXISTS confidence_score
    """)
    op.execute("""
        DROP INDEX IF EXISTS ix_analyses_upload_timestamp
    """)