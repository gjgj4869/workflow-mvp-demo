"""Initial schema

Revision ID: 88344c1d9134
Revises:
Create Date: 2024-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '88344c1d9134'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_workflows_name'), 'workflows', ['name'], unique=True)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('python_callable', sa.Text(), nullable=False),
        sa.Column('params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('retry_delay', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'name', name='uq_workflow_task_name')
    )
    op.create_index(op.f('ix_tasks_name'), 'tasks', ['name'], unique=False)

    # Create job_runs table
    op.create_table(
        'job_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dag_run_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('logs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dag_run_id')
    )
    op.create_index(op.f('ix_job_runs_dag_run_id'), 'job_runs', ['dag_run_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_runs_dag_run_id'), table_name='job_runs')
    op.drop_table('job_runs')
    op.drop_index(op.f('ix_tasks_name'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_workflows_name'), table_name='workflows')
    op.drop_table('workflows')
