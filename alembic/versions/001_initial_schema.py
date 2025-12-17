"""Initial schema for FKG-Core.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create entities table
    op.create_table(
        "entities",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False, server_default="v0.1"),
        sa.Column("authority_id", sa.String(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entities_type", "entities", ["type"])
    op.create_index("ix_entities_authority_id", "entities", ["authority_id"])
    op.create_index("ix_entities_type_authority", "entities", ["type", "authority_id"])
    op.create_index(
        "ix_entities_data_name",
        "entities",
        ["data"],
        postgresql_using="gin",
    )

    # Create edges table
    op.create_table(
        "edges",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("src_id", sa.String(), nullable=False),
        sa.Column("dst_id", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False, server_default="v0.1"),
        sa.Column("authority_id", sa.String(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edges_type", "edges", ["type"])
    op.create_index("ix_edges_src_id", "edges", ["src_id"])
    op.create_index("ix_edges_dst_id", "edges", ["dst_id"])
    op.create_index("ix_edges_authority_id", "edges", ["authority_id"])
    op.create_index("ix_edges_src_type", "edges", ["src_id", "type"])
    op.create_index("ix_edges_dst_type", "edges", ["dst_id", "type"])
    op.create_index("ix_edges_authority_type", "edges", ["authority_id", "type"])

    # Create sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create evidence table
    op.create_table(
        "evidence",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_entity_id", "evidence", ["entity_id"])
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"])

    # Create events table (append-only changelog)
    op.create_table(
        "events",
        sa.Column("seq", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("authority_id", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("seq"),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_authority_id", "events", ["authority_id"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("evidence")
    op.drop_table("sources")
    op.drop_table("edges")
    op.drop_table("entities")
