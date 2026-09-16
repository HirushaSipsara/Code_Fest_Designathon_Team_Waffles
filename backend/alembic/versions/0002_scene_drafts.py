"""store validated AI drafts for confirmation integrity

Revision ID: 0002_scene_drafts
Revises: 0001_cp3_slice
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_scene_drafts"
down_revision = "0001_cp3_slice"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("scene_drafts", sa.Column("id", sa.String(36), primary_key=True), sa.Column("role", sa.String(20), nullable=False), sa.Column("proposal", sa.JSON(), nullable=False), sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))

def downgrade():
    op.drop_table("scene_drafts")
