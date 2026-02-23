"""Phase 4: Upgrade to text-embedding-3-large (2000 dims) and HNSW index

Revision ID: a1b2c3d4e5f6
Revises: 00d96309f8ce
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '00d96309f8ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing IVFFlat index
    op.drop_index('idx_chunks_embedding', table_name='document_chunks')

    # 2. Clear all existing embeddings (they're 1536-dim, incompatible with new 2000-dim)
    op.execute("UPDATE document_chunks SET embedding = NULL")

    # 3. Alter embedding column from Vector(1536) to Vector(2000)
    #    text-embedding-3-large with dimensions=2000 (pgvector 0.6.0 HNSW max)
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(2000)")

    # 4. Add parent_chunk_id column for parent-child chunking
    op.add_column('document_chunks', sa.Column('parent_chunk_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_chunks_parent',
        'document_chunks', 'document_chunks',
        ['parent_chunk_id'], ['id'],
        ondelete='CASCADE'
    )

    # 5. Create HNSW index (better than IVFFlat for datasets under 100K rows)
    op.execute("""
        CREATE INDEX idx_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    # Drop HNSW index
    op.drop_index('idx_chunks_embedding_hnsw', table_name='document_chunks')

    # Remove parent_chunk_id
    op.drop_constraint('fk_chunks_parent', 'document_chunks', type_='foreignkey')
    op.drop_column('document_chunks', 'parent_chunk_id')

    # Revert embedding column to Vector(1536)
    op.execute("UPDATE document_chunks SET embedding = NULL")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536)")

    # Recreate IVFFlat index
    op.execute("""
        CREATE INDEX idx_chunks_embedding
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
