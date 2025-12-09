"""add prompt_profiles

Revision ID: d5e8f2a9b1c3
Revises: 9ff57d084d8a
Create Date: 2025-12-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5e8f2a9b1c3'
down_revision = '979750027763'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create prompt_profiles table
    op.create_table(
        'prompt_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('rag_system_prompt_template', sa.Text(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='512'),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='128'),
        sa.Column('top_k_chunks', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('semantic_search_ratio', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('relevance_threshold', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('llm_model_id', sa.String(length=100), nullable=False, server_default='amazon.nova-lite-v1:0'),
        sa.Column('llm_temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('llm_top_p', sa.Float(), nullable=False, server_default='0.9'),
        sa.Column('llm_max_tokens', sa.Integer(), nullable=False, server_default='2048'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('chunk_size >= 100 AND chunk_size <= 2000', name='check_chunk_size_range'),
        sa.CheckConstraint('chunk_overlap >= 0 AND chunk_overlap <= 500', name='check_chunk_overlap_range'),
        sa.CheckConstraint('chunk_overlap < chunk_size', name='check_chunk_overlap_less_than_size'),
        sa.CheckConstraint('top_k_chunks >= 1 AND top_k_chunks <= 50', name='check_top_k_range'),
        sa.CheckConstraint('semantic_search_ratio >= 0.0 AND semantic_search_ratio <= 1.0', name='check_semantic_ratio_range'),
        sa.CheckConstraint('relevance_threshold >= 0.0 AND relevance_threshold <= 1.0', name='check_relevance_threshold_range'),
        sa.CheckConstraint('llm_temperature >= 0.0 AND llm_temperature <= 1.0', name='check_temperature_range'),
        sa.CheckConstraint('llm_top_p >= 0.0 AND llm_top_p <= 1.0', name='check_top_p_range'),
        sa.CheckConstraint('llm_max_tokens >= 256 AND llm_max_tokens <= 4096', name='check_max_tokens_range'),
    )

    # Create indexes
    op.create_index('idx_profile_user_name', 'prompt_profiles', ['user_id', 'name'], unique=True)
    op.create_index('idx_profile_user_id', 'prompt_profiles', ['user_id'], unique=False)
    op.create_index('idx_profile_is_default', 'prompt_profiles', ['is_default'], unique=False)
    op.create_index('idx_profile_user_default', 'prompt_profiles', ['user_id', 'is_default'], unique=False)

    # Add profile_id to conversations table
    op.add_column('conversations', sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_conversation_profile_id', 'conversations', ['profile_id'], unique=False)
    op.create_foreign_key('fk_conversation_profile', 'conversations', 'prompt_profiles', ['profile_id'], ['id'], ondelete='SET NULL')

    # Add profile_id to documents table
    op.add_column('documents', sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_document_profile_id', 'documents', ['profile_id'], unique=False)
    op.create_foreign_key('fk_document_profile', 'documents', 'prompt_profiles', ['profile_id'], ['id'], ondelete='SET NULL')

    # Data migration: Create default profiles for existing users and link existing data
    # This will be done via a separate data migration script or SQL
    # For now, we leave profile_id as nullable for backward compatibility


def downgrade() -> None:
    # Drop foreign keys and columns from documents
    op.drop_constraint('fk_document_profile', 'documents', type_='foreignkey')
    op.drop_index('idx_document_profile_id', table_name='documents')
    op.drop_column('documents', 'profile_id')

    # Drop foreign keys and columns from conversations
    op.drop_constraint('fk_conversation_profile', 'conversations', type_='foreignkey')
    op.drop_index('idx_conversation_profile_id', table_name='conversations')
    op.drop_column('conversations', 'profile_id')

    # Drop indexes on prompt_profiles
    op.drop_index('idx_profile_user_default', table_name='prompt_profiles')
    op.drop_index('idx_profile_is_default', table_name='prompt_profiles')
    op.drop_index('idx_profile_user_id', table_name='prompt_profiles')
    op.drop_index('idx_profile_user_name', table_name='prompt_profiles')

    # Drop prompt_profiles table
    op.drop_table('prompt_profiles')
