"""persist AI-created maintenance work items

Revision ID: 0003_maintenance_requests
Revises: 0002_scene_drafts
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_maintenance_requests"
down_revision = "0002_scene_drafts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit", sa.String(20), nullable=False, server_default="1204"),
        sa.Column("device_id", sa.String(50), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("decision", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_maintenance_requests_device_id", "maintenance_requests", ["device_id"])


def downgrade():
    op.drop_index("ix_maintenance_requests_device_id", table_name="maintenance_requests")
    op.drop_table("maintenance_requests")
