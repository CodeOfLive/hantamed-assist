import sqlalchemy as sa
from alembic import op

revision = '001_init'
down_revision = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), server_default='user'),
        sa.Column('password_change_required', sa.Boolean, server_default='false')
    )
    op.create_table('drugs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('active_ingredient', sa.String(100)),
        sa.Column('indication', sa.Text),
        sa.Column('side_effects', sa.Text),
        sa.Column('source', sa.String(200))
    )
    op.create_table('analyses',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('image_hash', sa.String(64), nullable=False),
        sa.Column('file_size_kb', sa.Float),
        sa.Column('image_format', sa.String(10)),
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('upload_timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('relevance_score', sa.Float),
        sa.Column('avg_confidence', sa.Float),
        sa.Column('status', sa.String(20), server_default='accepted'),
        sa.Column('extracted_entities', sa.Text),
        sa.Column('model_version', sa.String(20)),
        sa.Column('latency_ms', sa.Float),
        sa.Column('qa_summary', sa.Text)
    )
    op.create_table('system_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('level', sa.String(10), server_default='INFO'),
        sa.Column('message', sa.Text),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('endpoint', sa.String(50)),
        sa.Column('latency_ms', sa.Float)
    )

def downgrade():
    op.drop_table('system_logs')
    op.drop_table('analyses')
    op.drop_table('drugs')
    op.drop_table('users')