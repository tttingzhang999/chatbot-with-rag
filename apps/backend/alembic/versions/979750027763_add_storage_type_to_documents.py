"""add storage_type to documents

Revision ID: 979750027763
Revises: 9ff57d084d8a
Create Date: 2025-12-09 10:36:29.141325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '979750027763'
down_revision = '9ff57d084d8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add storage_type column as nullable first
    op.add_column('documents', sa.Column('storage_type', sa.String(10), nullable=True))

    # Migrate existing data: infer from file_path
    op.execute("""
        UPDATE documents
        SET storage_type = CASE
            WHEN file_path LIKE 's3://%' THEN 'cloud'
            ELSE 'local'
        END
    """)

    # Make non-nullable after data migration
    op.alter_column('documents', 'storage_type', nullable=False)


def downgrade() -> None:
    op.drop_column('documents', 'storage_type')
