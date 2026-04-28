"""create stock movements table

Revision ID: f4d6a8b7c9e1
Revises: c6da4811668d
Create Date: 2026-04-19 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4d6a8b7c9e1"
down_revision: Union[str, Sequence[str], None] = "c6da4811668d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Float(), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_movements_id"), "stock_movements", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stock_movements_id"), table_name="stock_movements")
    op.drop_table("stock_movements")
