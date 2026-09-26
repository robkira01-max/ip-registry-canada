"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-09-26 00:00:00.000000

Crée les 7 tables du schéma initial Registre IP Canada :
  users, audit_logs, patents, trademarks, copyrights,
  industrial_designs, ip_documents
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    now_expr = sa.text("NOW()" if is_pg else "CURRENT_TIMESTAMP")

    # ── Enums PostgreSQL ──────────────────────────────────────────────────────
    if is_pg:
        op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('admin','agent','readonly'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE auditaction AS ENUM ('USER_LOGIN','USER_LOGOUT','USER_CREATED','LOGIN_FAILED','PATENT_CREATED','PATENT_UPDATED','PATENT_PUBLISHED','PATENT_GRANTED','PATENT_ABANDONED','TRADEMARK_CREATED','TRADEMARK_UPDATED','TRADEMARK_PUBLISHED','TRADEMARK_REGISTERED','TRADEMARK_ABANDONED','COPYRIGHT_REGISTERED','COPYRIGHT_UPDATED','DESIGN_CREATED','DESIGN_UPDATED','DESIGN_REGISTERED','DOCUMENT_UPLOADED','DOCUMENT_DELETED','SEARCH_PERFORMED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE patentstatus AS ENUM ('draft','filed','published','examination','granted','abandoned','expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE patenttype AS ENUM ('utility','divisional','continuation','pct'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE trademarkstatus AS ENUM ('draft','filed','advertised','registered','abandoned','expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE trademarktype AS ENUM ('word','design','word_design','certification','distinguishing_guise'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE copyrightworktype AS ENUM ('literary','artistic','musical','dramatic','sound_recording','performance','communication_signal'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE copyrightstatus AS ENUM ('active','expired','disputed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE designstatus AS ENUM ('draft','filed','registered','abandoned','expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        op.execute("DO $$ BEGIN CREATE TYPE documentcategory AS ENUM ('specification','drawing','certificate','correspondence','fee_receipt','assignment','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              sa.Integer(),    nullable=False),
        sa.Column("username",        sa.String(64),   nullable=False),
        sa.Column("email",           sa.String(128),  nullable=False),
        sa.Column("hashed_password", sa.String(256),  nullable=False),
        sa.Column("role",            sa.Enum("admin", "agent", "readonly", name="userrole"), nullable=False, server_default="readonly"),
        sa.Column("is_active",       sa.Boolean(),    nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.Column("last_login",      sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id",       "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email",    "users", ["email"],    unique=True)

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id",            sa.Integer(),   nullable=False),
        sa.Column("action",        sa.Enum("USER_LOGIN","USER_LOGOUT","USER_CREATED","LOGIN_FAILED","PATENT_CREATED","PATENT_UPDATED","PATENT_PUBLISHED","PATENT_GRANTED","PATENT_ABANDONED","TRADEMARK_CREATED","TRADEMARK_UPDATED","TRADEMARK_PUBLISHED","TRADEMARK_REGISTERED","TRADEMARK_ABANDONED","COPYRIGHT_REGISTERED","COPYRIGHT_UPDATED","DESIGN_CREATED","DESIGN_UPDATED","DESIGN_REGISTERED","DOCUMENT_UPLOADED","DOCUMENT_DELETED","SEARCH_PERFORMED", name="auditaction"), nullable=False),
        sa.Column("user_username", sa.String(64),  nullable=False),
        sa.Column("ip_address",    sa.String(45),  nullable=True),
        sa.Column("resource_type", sa.String(32),  nullable=True),
        sa.Column("resource_id",   sa.Integer(),   nullable=True),
        sa.Column("details",       sa.JSON(),      nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_id",           "audit_logs", ["id"])
    op.create_index("ix_audit_logs_action",       "audit_logs", ["action"])
    op.create_index("ix_audit_logs_user_username","audit_logs", ["user_username"])
    op.create_index("ix_audit_logs_created_at",   "audit_logs", ["created_at"])

    # ── patents ───────────────────────────────────────────────────────────────
    op.create_table(
        "patents",
        sa.Column("id",                sa.Integer(),    nullable=False),
        sa.Column("application_number",sa.String(32),   nullable=True),
        sa.Column("patent_number",     sa.String(32),   nullable=True),
        sa.Column("pct_number",        sa.String(32),   nullable=True),
        sa.Column("patent_type",       sa.Enum("utility","divisional","continuation","pct", name="patenttype"), nullable=False, server_default="utility"),
        sa.Column("status",            sa.Enum("draft","filed","published","examination","granted","abandoned","expired", name="patentstatus"), nullable=False, server_default="draft"),
        sa.Column("title_fr",          sa.String(512),  nullable=False),
        sa.Column("title_en",          sa.String(512),  nullable=True),
        sa.Column("abstract_fr",       sa.Text(),       nullable=True),
        sa.Column("abstract_en",       sa.Text(),       nullable=True),
        sa.Column("claims",            sa.Text(),       nullable=True),
        sa.Column("ipc_codes",         sa.JSON(),       nullable=True),
        sa.Column("inventors",         sa.JSON(),       nullable=True),
        sa.Column("owners",            sa.JSON(),       nullable=True),
        sa.Column("filing_date",       sa.Date(),       nullable=True),
        sa.Column("publication_date",  sa.Date(),       nullable=True),
        sa.Column("grant_date",        sa.Date(),       nullable=True),
        sa.Column("expiry_date",       sa.Date(),       nullable=True),
        sa.Column("priority_date",     sa.Date(),       nullable=True),
        sa.Column("priority_country",  sa.String(4),    nullable=True),
        sa.Column("maintenance_fees_paid_until",  sa.Date(), nullable=True),
        sa.Column("next_maintenance_fee_due",     sa.Date(), nullable=True),
        sa.Column("is_canadian_origin",sa.Boolean(),    nullable=False, server_default=sa.text("true")),
        sa.Column("agent_notes",       sa.Text(),       nullable=True),
        sa.Column("cipo_data",         sa.JSON(),       nullable=True),
        sa.Column("created_by_id",     sa.Integer(),    nullable=False),
        sa.Column("created_at",        sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.Column("updated_at",        sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.UniqueConstraint("application_number"),
        sa.UniqueConstraint("patent_number"),
    )
    op.create_index("ix_patents_id",             "patents", ["id"])
    op.create_index("ix_patents_status",         "patents", ["status"])
    op.create_index("ix_patents_status_filing",  "patents", ["status", "filing_date"])

    # ── trademarks ────────────────────────────────────────────────────────────
    op.create_table(
        "trademarks",
        sa.Column("id",                  sa.Integer(),    nullable=False),
        sa.Column("application_number",  sa.String(32),   nullable=True),
        sa.Column("registration_number", sa.String(32),   nullable=True),
        sa.Column("madrid_number",       sa.String(32),   nullable=True),
        sa.Column("trademark_type",      sa.Enum("word","design","word_design","certification","distinguishing_guise", name="trademarktype"), nullable=False, server_default="word"),
        sa.Column("status",              sa.Enum("draft","filed","advertised","registered","abandoned","expired", name="trademarkstatus"), nullable=False, server_default="draft"),
        sa.Column("mark_text",           sa.String(512),  nullable=True),
        sa.Column("description_fr",      sa.Text(),       nullable=True),
        sa.Column("description_en",      sa.Text(),       nullable=True),
        sa.Column("nice_classes",        sa.JSON(),       nullable=True),
        sa.Column("colors_claimed",      sa.String(256),  nullable=True),
        sa.Column("owners",              sa.JSON(),       nullable=True),
        sa.Column("filing_date",         sa.Date(),       nullable=True),
        sa.Column("advertisement_date",  sa.Date(),       nullable=True),
        sa.Column("registration_date",   sa.Date(),       nullable=True),
        sa.Column("renewal_date",        sa.Date(),       nullable=True),
        sa.Column("expiry_date",         sa.Date(),       nullable=True),
        sa.Column("use_in_canada_since", sa.Date(),       nullable=True),
        sa.Column("is_used_in_canada",   sa.Boolean(),    nullable=False, server_default=sa.text("false")),
        sa.Column("agent_notes",         sa.Text(),       nullable=True),
        sa.Column("cipo_data",           sa.JSON(),       nullable=True),
        sa.Column("design_file_path",    sa.String(512),  nullable=True),
        sa.Column("created_by_id",       sa.Integer(),    nullable=False),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.UniqueConstraint("application_number"),
        sa.UniqueConstraint("registration_number"),
    )
    op.create_index("ix_trademarks_id",            "trademarks", ["id"])
    op.create_index("ix_trademarks_status",        "trademarks", ["status"])
    op.create_index("ix_trademarks_status_filing", "trademarks", ["status", "filing_date"])

    # ── copyrights ────────────────────────────────────────────────────────────
    op.create_table(
        "copyrights",
        sa.Column("id",                  sa.Integer(),    nullable=False),
        sa.Column("registration_number", sa.String(32),   nullable=True),
        sa.Column("work_type",           sa.Enum("literary","artistic","musical","dramatic","sound_recording","performance","communication_signal", name="copyrightworktype"), nullable=False, server_default="literary"),
        sa.Column("status",              sa.Enum("active","expired","disputed", name="copyrightstatus"), nullable=False, server_default="active"),
        sa.Column("title",               sa.String(512),  nullable=False),
        sa.Column("description",         sa.Text(),       nullable=True),
        sa.Column("is_published",        sa.Boolean(),    nullable=False, server_default=sa.text("false")),
        sa.Column("authors",             sa.JSON(),       nullable=True),
        sa.Column("owners",              sa.JSON(),       nullable=True),
        sa.Column("is_work_for_hire",    sa.Boolean(),    nullable=False, server_default=sa.text("false")),
        sa.Column("creation_date",       sa.Date(),       nullable=True),
        sa.Column("publication_date",    sa.Date(),       nullable=True),
        sa.Column("registration_date",   sa.Date(),       nullable=True),
        sa.Column("expiry_date",         sa.Date(),       nullable=True),
        sa.Column("license_type",        sa.String(64),   nullable=True),
        sa.Column("license_notes",       sa.Text(),       nullable=True),
        sa.Column("agent_notes",         sa.Text(),       nullable=True),
        sa.Column("cipo_data",           sa.JSON(),       nullable=True),
        sa.Column("created_by_id",       sa.Integer(),    nullable=False),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.UniqueConstraint("registration_number"),
    )
    op.create_index("ix_copyrights_id",     "copyrights", ["id"])
    op.create_index("ix_copyrights_status", "copyrights", ["status"])

    # ── industrial_designs ────────────────────────────────────────────────────
    op.create_table(
        "industrial_designs",
        sa.Column("id",                  sa.Integer(),    nullable=False),
        sa.Column("application_number",  sa.String(32),   nullable=True),
        sa.Column("registration_number", sa.String(32),   nullable=True),
        sa.Column("status",              sa.Enum("draft","filed","registered","abandoned","expired", name="designstatus"), nullable=False, server_default="draft"),
        sa.Column("title",               sa.String(512),  nullable=False),
        sa.Column("description",         sa.Text(),       nullable=True),
        sa.Column("article_name",        sa.String(256),  nullable=True),
        sa.Column("locarno_classes",     sa.JSON(),       nullable=True),
        sa.Column("creators",            sa.JSON(),       nullable=True),
        sa.Column("owners",              sa.JSON(),       nullable=True),
        sa.Column("filing_date",         sa.Date(),       nullable=True),
        sa.Column("registration_date",   sa.Date(),       nullable=True),
        sa.Column("first_renewal_date",  sa.Date(),       nullable=True),
        sa.Column("expiry_date",         sa.Date(),       nullable=True),
        sa.Column("image_paths",         sa.JSON(),       nullable=True),
        sa.Column("agent_notes",         sa.Text(),       nullable=True),
        sa.Column("cipo_data",           sa.JSON(),       nullable=True),
        sa.Column("created_by_id",       sa.Integer(),    nullable=False),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.UniqueConstraint("application_number"),
        sa.UniqueConstraint("registration_number"),
    )
    op.create_index("ix_industrial_designs_id",     "industrial_designs", ["id"])
    op.create_index("ix_industrial_designs_status", "industrial_designs", ["status"])

    # ── ip_documents ──────────────────────────────────────────────────────────
    op.create_table(
        "ip_documents",
        sa.Column("id",              sa.Integer(),    nullable=False),
        sa.Column("resource_type",   sa.String(16),   nullable=False),
        sa.Column("resource_id",     sa.Integer(),    nullable=False),
        sa.Column("category",        sa.Enum("specification","drawing","certificate","correspondence","fee_receipt","assignment","other", name="documentcategory"), nullable=False, server_default="other"),
        sa.Column("filename",        sa.String(512),  nullable=False),
        sa.Column("file_path",       sa.String(512),  nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type",       sa.String(128),  nullable=False),
        sa.Column("hash_sha256",     sa.String(64),   nullable=False),
        sa.Column("uploaded_by_id",  sa.Integer(),    nullable=False),
        sa.Column("uploaded_at",     sa.DateTime(timezone=True), nullable=False, server_default=now_expr),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
    )
    op.create_index("ix_ip_documents_id",            "ip_documents", ["id"])
    op.create_index("ix_ip_documents_resource_type", "ip_documents", ["resource_type"])
    op.create_index("ix_ip_documents_resource_id",   "ip_documents", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_ip_documents_resource_id",   "ip_documents")
    op.drop_index("ix_ip_documents_resource_type", "ip_documents")
    op.drop_index("ix_ip_documents_id",            "ip_documents")
    op.drop_table("ip_documents")

    op.drop_index("ix_industrial_designs_status", "industrial_designs")
    op.drop_index("ix_industrial_designs_id",     "industrial_designs")
    op.drop_table("industrial_designs")

    op.drop_index("ix_copyrights_status", "copyrights")
    op.drop_index("ix_copyrights_id",     "copyrights")
    op.drop_table("copyrights")

    op.drop_index("ix_trademarks_status_filing", "trademarks")
    op.drop_index("ix_trademarks_status",        "trademarks")
    op.drop_index("ix_trademarks_id",            "trademarks")
    op.drop_table("trademarks")

    op.drop_index("ix_patents_status_filing", "patents")
    op.drop_index("ix_patents_status",        "patents")
    op.drop_index("ix_patents_id",            "patents")
    op.drop_table("patents")

    op.drop_index("ix_audit_logs_created_at",    "audit_logs")
    op.drop_index("ix_audit_logs_user_username", "audit_logs")
    op.drop_index("ix_audit_logs_action",        "audit_logs")
    op.drop_index("ix_audit_logs_id",            "audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_users_email",    "users")
    op.drop_index("ix_users_username", "users")
    op.drop_index("ix_users_id",       "users")
    op.drop_table("users")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for t in ["documentcategory","designstatus","copyrightstatus","copyrightworktype",
                  "trademarktype","trademarkstatus","patenttype","patentstatus",
                  "auditaction","userrole"]:
            op.execute(f"DROP TYPE IF EXISTS {t}")
