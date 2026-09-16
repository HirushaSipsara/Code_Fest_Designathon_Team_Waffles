"""create CP3 device, scene and activity tables

Revision ID: 0001_cp3_slice
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_cp3_slice"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("devices", sa.Column("id", sa.String(50), primary_key=True), sa.Column("name", sa.String(100), nullable=False), sa.Column("kind", sa.String(30), nullable=False), sa.Column("room", sa.String(50), nullable=False), sa.Column("state", sa.JSON(), nullable=False))
    op.create_table("scenes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("trigger", sa.JSON(), nullable=False), sa.Column("conditions", sa.JSON(), nullable=False), sa.Column("actions", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("activity_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("message", sa.Text(), nullable=False), sa.Column("category", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))

def downgrade():
    op.drop_table("activity_events")
    op.drop_table("scenes")
    op.drop_table("devices")
