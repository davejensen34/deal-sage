"""link approved model research plans to frontier items"""

from alembic import op
import sqlalchemy as sa


revision = "a1c83d9f04b2"
down_revision = "d84a0c4e219f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("research_frontier_items") as batch_op:
        batch_op.add_column(sa.Column("proposal_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_research_frontier_items_proposal_id_model_proposals",
            "model_proposals",
            ["proposal_id"],
            ["id"],
        )
    op.create_index(
        "ix_research_frontier_items_proposal_id", "research_frontier_items", ["proposal_id"]
    )


def downgrade():
    op.drop_index("ix_research_frontier_items_proposal_id", table_name="research_frontier_items")
    with op.batch_alter_table("research_frontier_items") as batch_op:
        batch_op.drop_constraint(
            "fk_research_frontier_items_proposal_id_model_proposals", type_="foreignkey"
        )
        batch_op.drop_column("proposal_id")
