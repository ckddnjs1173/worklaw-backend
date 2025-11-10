from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "20251109_knowledge_core"
down_revision = None
branch_labels = None
depends_on = None

def _has_table(conn, name: str) -> bool:
    insp = inspect(conn)
    return insp.has_table(name)

def upgrade():
    conn = op.get_bind()

    # --- sources ---
    if not _has_table(conn, "sources"):
        op.create_table(
            "sources",
            sa.Column("source_key", sa.String(), primary_key=True),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("api_url", sa.String()),
            sa.Column("license", sa.String()),
            sa.Column("last_checked_at", sa.String()),
        )

    # --- sync_jobs ---
    if not _has_table(conn, "sync_jobs"):
        op.create_table(
            "sync_jobs",
            sa.Column("job_id", sa.String(), primary_key=True),
            sa.Column("source_key", sa.String(), nullable=False),
            sa.Column("started_at", sa.DateTime()),
            sa.Column("finished_at", sa.DateTime()),
            sa.Column("status", sa.String(), server_default="running"),
            sa.Column("items_upserted", sa.Integer(), server_default="0"),
            sa.Column("checksum", sa.String()),
            sa.Column("log", sa.Text()),
        )

    # --- staging_raw ---
    if not _has_table(conn, "staging_raw"):
        op.create_table(
            "staging_raw",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("source_key", sa.String(), nullable=False),
            sa.Column("natural_id", sa.String(), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("checksum", sa.String(), nullable=False),
            sa.Column("fetched_at", sa.DateTime()),
            sa.UniqueConstraint("source_key", "natural_id", name="uq_staging_source_natural"),
        )

    # --- laws ---
    if not _has_table(conn, "laws"):
        op.create_table(
            "laws",
            sa.Column("law_id", sa.String(), primary_key=True),
            sa.Column("law_name_kr", sa.String(), nullable=False),
            sa.Column("law_name_en", sa.String()),
            sa.Column("status", sa.String()),
        )

    # --- law_versions ---
    if not _has_table(conn, "law_versions"):
        op.create_table(
            "law_versions",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("law_id", sa.String(), nullable=False),
            sa.Column("version_no", sa.String(), nullable=False),
            sa.Column("effective_from", sa.String()),
            sa.Column("effective_to", sa.String()),
            sa.Column("source_ref", sa.String()),
            sa.UniqueConstraint("law_id", "version_no", name="uq_law_id_version_no"),
        )

    # --- law_articles ---
    if not _has_table(conn, "law_articles"):
        op.create_table(
            "law_articles",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("law_id", sa.String(), nullable=False),
            sa.Column("version_no", sa.String(), nullable=False),
            sa.Column("article_no", sa.String(), nullable=False),
            sa.Column("title", sa.String()),
            sa.Column("body_html", sa.Text()),
            sa.Column("body_text", sa.Text()),
            sa.Column("updated_at", sa.String()),
            sa.UniqueConstraint("law_id", "version_no", "article_no", name="uq_law_ver_article"),
        )

    # --- minimum_wage_history ---
    if not _has_table(conn, "minimum_wage_history"):
        op.create_table(
            "minimum_wage_history",
            sa.Column("year", sa.Integer(), primary_key=True),
            sa.Column("hourly", sa.Integer(), nullable=False),
            sa.Column("monthly_209h", sa.Integer()),
            sa.Column("notice_no", sa.String()),
            sa.Column("notice_date", sa.String()),
            sa.Column("source_url", sa.String()),
        )

    # --- admin_interpretations ---
    if not _has_table(conn, "admin_interpretations"):
        op.create_table(
            "admin_interpretations",
            sa.Column("interp_id", sa.String(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("asked_at", sa.String()),
            sa.Column("answered_at", sa.String()),
            sa.Column("question", sa.Text()),
            sa.Column("answer", sa.Text()),
            sa.Column("law_id", sa.String()),
            sa.Column("article_no", sa.String()),
            sa.Column("source_url", sa.String()),
            sa.Column("tags", sa.String()),
        )

    # --- holidays ---
    if not _has_table(conn, "holidays"):
        op.create_table(
            "holidays",
            sa.Column("date", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("type", sa.String()),
            sa.Column("is_public", sa.Boolean(), server_default=sa.text("1")),
            sa.Column("source_ref", sa.String()),
        )

    # --- policy_bulletins ---
    if not _has_table(conn, "policy_bulletins"):
        op.create_table(
            "policy_bulletins",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("effective_date", sa.String()),
            sa.Column("audience", sa.String()),
            sa.Column("category", sa.String()),
            sa.Column("summary_md", sa.Text()),
            sa.Column("law_id", sa.String()),
            sa.Column("article_no", sa.String()),
            sa.Column("source_url", sa.String()),
            sa.Column("tags", sa.String()),
        )


def downgrade():
    conn = op.get_bind()
    # 드롭은 존재할 때만
    for name in [
        "policy_bulletins",
        "holidays",
        "admin_interpretations",
        "minimum_wage_history",
        "law_articles",
        "law_versions",
        "laws",
        "staging_raw",
        "sync_jobs",
        "sources",
    ]:
        if inspect(conn).has_table(name):
            op.drop_table(name)
