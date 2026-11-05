"""Ajouter table users (authentification)

Revision ID: a1b2c3d4e5f6
Revises: fd9db0e2de3d
Create Date: 2026-11-05 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "fd9db0e2de3d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("nom_complet", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.Column("date_creation", sa.DateTime(), nullable=False),
        sa.Column("derniere_connexion", sa.DateTime(), nullable=True),
        sa.Column("echecs_connexion", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verrouille_jusqu_a", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_username"), ["username"], unique=True)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_username"))
    op.drop_table("users")
