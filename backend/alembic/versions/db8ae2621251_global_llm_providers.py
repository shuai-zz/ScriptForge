"""global llm providers

Revision ID: db8ae2621251
Revises: bb62ae6e7feb
Create Date: 2026-06-06 21:28:44.585082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'db8ae2621251'
down_revision: Union[str, Sequence[str], None] = 'bb62ae6e7feb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make llm_providers global: drop project scoping, enforce unique provider_id.

    Existing per-project rows are wiped — providers are reconfigured once
    globally from the home page.
    """
    # Wipe per-project rows first so dropping the column / adding the unique
    # constraint cannot collide on duplicate provider_id across old projects.
    op.execute("DELETE FROM llm_providers")
    op.drop_constraint(
        "llm_providers_project_id_fkey", "llm_providers", type_="foreignkey"
    )
    op.drop_column("llm_providers", "project_id")
    op.create_unique_constraint(
        "uq_llm_providers_provider_id", "llm_providers", ["provider_id"]
    )


def downgrade() -> None:
    """Best-effort revert (per-project rows are not restorable)."""
    op.drop_constraint(
        "uq_llm_providers_provider_id", "llm_providers", type_="unique"
    )
    op.add_column(
        "llm_providers",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "llm_providers_project_id_fkey",
        "llm_providers",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
