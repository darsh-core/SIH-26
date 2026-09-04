"""add_learning_modules_and_lessons

Revision ID: 9a01b2c3d4e5
Revises: dd1bc932975d
Create Date: 2026-09-04 19:22:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a01b2c3d4e5'
down_revision: Union[str, None] = '58033f0ff148'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create course_module table
    op.create_table(
        'course_module',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('course_id', sa.UUID(), sa.ForeignKey('course.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('course_id', 'code', name='uq_course_module_code')
    )
    op.create_index('ix_course_module_course_id', 'course_module', ['course_id'])

    # 2. Create course_lesson table
    op.create_table(
        'course_lesson',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('module_id', sa.UUID(), sa.ForeignKey('course_module.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_course_lesson_module_id', 'course_lesson', ['module_id'])

    # 3. Create learning_module_progress table
    op.create_table(
        'learning_module_progress',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('learning_progress_id', sa.UUID(), sa.ForeignKey('learning_progress.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.UUID(), sa.ForeignKey('course_module.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NOT_STARTED'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('learning_progress_id', 'module_id', name='uq_learning_module_progress')
    )
    op.create_index('ix_learning_module_progress_learning_progress_id', 'learning_module_progress', ['learning_progress_id'])
    op.create_index('ix_learning_module_progress_module_id', 'learning_module_progress', ['module_id'])


def downgrade() -> None:
    op.drop_index('ix_learning_module_progress_module_id', table_name='learning_module_progress')
    op.drop_index('ix_learning_module_progress_learning_progress_id', table_name='learning_module_progress')
    op.drop_table('learning_module_progress')

    op.drop_index('ix_course_lesson_module_id', table_name='course_lesson')
    op.drop_table('course_lesson')

    op.drop_index('ix_course_module_course_id', table_name='course_module')
    op.drop_table('course_module')
