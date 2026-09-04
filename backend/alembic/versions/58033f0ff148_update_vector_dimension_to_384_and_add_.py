"""update_vector_dimension_to_384_and_add_chunk_hash

Revision ID: 58033f0ff148
Revises: dd1bc932975d
Create Date: 2026-09-04 12:26:55.385292

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '58033f0ff148'
down_revision: Union[str, None] = 'dd1bc932975d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add chunk_hash to document_chunk for idempotency & deduplication
    op.add_column('document_chunk', sa.Column('chunk_hash', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_document_chunk_chunk_hash'), 'document_chunk', ['chunk_hash'], unique=False)

    # 2. Reset placeholder/mock embeddings and update vector column to canonical dimension 384
    op.execute("DELETE FROM document_embedding;")
    op.execute("ALTER TABLE document_embedding ALTER COLUMN embedding TYPE vector(384);")


def downgrade() -> None:
    op.execute("DELETE FROM document_embedding;")
    op.execute("ALTER TABLE document_embedding ALTER COLUMN embedding TYPE vector(1536);")
    op.drop_index(op.f('ix_document_chunk_chunk_hash'), table_name='document_chunk')
    op.drop_column('document_chunk', 'chunk_hash')
