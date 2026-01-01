"""Add Git integration fields to Workflow and Task models

Revision ID: 2a3cef5e97c1
Revises: 88344c1d9134
Create Date: 2025-12-30 00:58:34.719950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a3cef5e97c1'
down_revision: Union[str, None] = '88344c1d9134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Git integration fields to workflows table
    op.add_column('workflows', sa.Column('git_repository', sa.String(length=500), nullable=True))
    op.add_column('workflows', sa.Column('git_branch', sa.String(length=255), nullable=True, server_default='main'))
    op.add_column('workflows', sa.Column('git_commit_sha', sa.String(length=40), nullable=True))
    op.add_column('workflows', sa.Column('git_auth_type', sa.String(length=50), nullable=True, server_default='none'))

    # Add Git integration fields to tasks table
    op.add_column('tasks', sa.Column('script_path', sa.String(length=500), nullable=True))
    op.add_column('tasks', sa.Column('function_name', sa.String(length=255), nullable=True))

    # Make python_callable nullable since it's now optional (can use Git instead)
    op.alter_column('tasks', 'python_callable', nullable=True)


def downgrade() -> None:
    # Remove Git integration fields from tasks table
    op.drop_column('tasks', 'function_name')
    op.drop_column('tasks', 'script_path')

    # Remove Git integration fields from workflows table
    op.drop_column('workflows', 'git_auth_type')
    op.drop_column('workflows', 'git_commit_sha')
    op.drop_column('workflows', 'git_branch')
    op.drop_column('workflows', 'git_repository')

    # Restore python_callable to non-nullable
    op.alter_column('tasks', 'python_callable', nullable=False)
