"""v2_schema_overhaul

Revision ID: a9bd4c354db9
Revises:
Create Date: 2026-04-23 18:51:38.411421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT, JSON, ENUM


# revision identifiers, used by Alembic.
revision: str = 'a9bd4c354db9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema from v1 to v2."""
    conn = op.get_bind()

    # ===== 4.1 DROP v1 tables =====
    op.execute("DROP TABLE IF EXISTS SS_CACHED_PLANS")
    op.execute("DROP TABLE IF EXISTS SS_GOAL_TEMPLATES")
    op.execute("DROP TABLE IF EXISTS SS_USER_PLANS")
    op.execute("DROP TABLE IF EXISTS SMALLSTEP_ACTIVITIES")
    op.execute("DROP TABLE IF EXISTS SMALLSTEP_GAME_DATA")

    # ===== 4.3 ALTER SMALLSTEP_USERS =====
    # Check if columns exist before dropping (for idempotency)
    existing_cols = [row[0] for row in conn.execute(sa.text("SHOW COLUMNS FROM SMALLSTEP_USERS")).fetchall()]

    cols_to_drop = ['PHONE', 'PROFILE_IMAGE', 'LAST_LOGIN', 'IS_ACTIVE', 'PREFERRED_LANGUAGE', 'TIMEZONE']
    for col in cols_to_drop:
        if col in existing_cols:
            op.execute(f"ALTER TABLE SMALLSTEP_USERS DROP COLUMN {col}")

    # Add new columns if they don't exist
    if 'LEVEL' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('LEVEL', INTEGER(11), default=1, server_default=sa.text('1')))
    if 'CURRENT_STREAK' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('CURRENT_STREAK', INTEGER(11), default=0, server_default=sa.text('0')))
    if 'LONGEST_STREAK' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('LONGEST_STREAK', INTEGER(11), default=0, server_default=sa.text('0')))
    if 'NOTIFICATION_ENABLED' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('NOTIFICATION_ENABLED', sa.Boolean, default=True, server_default=sa.text('1')))
    if 'NOTIFICATION_TIME' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('NOTIFICATION_TIME', sa.String(10), nullable=True))
    if 'DAILY_AVAILABLE_TIME' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('DAILY_AVAILABLE_TIME', INTEGER(11), nullable=True))
    if 'EXPERIENCE_POINTS' not in existing_cols:
        op.add_column('SMALLSTEP_USERS', sa.Column('EXPERIENCE_POINTS', INTEGER(11), default=0, server_default=sa.text('0')))

    # ===== 4.3 ALTER SMALLSTEP_GOALS =====
    existing_goal_cols = [row[0] for row in conn.execute(sa.text("SHOW COLUMNS FROM SMALLSTEP_GOALS")).fetchall()]

    goal_cols_to_drop = ['CATEGORY', 'PRIORITY', 'REPEATABLE', 'MAX_PROGRESS', 'PARTICIPANTS']
    for col in goal_cols_to_drop:
        if col in existing_goal_cols:
            op.execute(f"ALTER TABLE SMALLSTEP_GOALS DROP COLUMN {col}")

    if 'GOAL_TEXT' not in existing_goal_cols:
        op.add_column('SMALLSTEP_GOALS', sa.Column('GOAL_TEXT', LONGTEXT, nullable=False))
    if 'GOAL_TYPE' not in existing_goal_cols:
        op.add_column('SMALLSTEP_GOALS', sa.Column('GOAL_TYPE', ENUM('DEADLINE', 'ONGOING'), default='ONGOING', server_default=sa.text("'ONGOING'")))
    if 'STATUS' not in existing_goal_cols:
        op.add_column('SMALLSTEP_GOALS', sa.Column('STATUS', ENUM('ACTIVE', 'MAINTAIN', 'PAUSED', 'COMPLETED', 'ARCHIVED'), default='ACTIVE', server_default=sa.text("'ACTIVE'")))
    if 'DEADLINE_DATE' not in existing_goal_cols:
        op.add_column('SMALLSTEP_GOALS', sa.Column('DEADLINE_DATE', sa.DateTime, nullable=True))
    if 'CURRENT_LEVEL' not in existing_goal_cols:
        op.add_column('SMALLSTEP_GOALS', sa.Column('CURRENT_LEVEL', INTEGER(11), default=1, server_default=sa.text('1')))

    # ===== 4.2 CREATE v2 tables =====

    # SMALLSTEP_PHASES
    op.create_table(
        'SMALLSTEP_PHASES',
        sa.Column('ID', INTEGER(11), primary_key=True, autoincrement=True),
        sa.Column('GOAL_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_GOALS.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('PHASE_ORDER', INTEGER(11), nullable=False),
        sa.Column('PHASE_TITLE', sa.String(200), nullable=False),
        sa.Column('PHASE_DESCRIPTION', LONGTEXT, nullable=True),
        sa.Column('ESTIMATED_WEEKS', INTEGER(11), nullable=True),
        sa.Column('STATUS', ENUM('PENDING', 'ACTIVE', 'COMPLETED'), default='PENDING', server_default=sa.text("'PENDING'")),
        sa.Column('STARTED_AT', sa.DateTime, nullable=True),
        sa.Column('COMPLETED_AT', sa.DateTime, nullable=True),
        sa.Column('CREATED_AT', sa.DateTime, nullable=False, server_default=sa.text('current_timestamp()')),
    )

    # SMALLSTEP_WEEKLY_PLANS
    op.create_table(
        'SMALLSTEP_WEEKLY_PLANS',
        sa.Column('ID', INTEGER(11), primary_key=True, autoincrement=True),
        sa.Column('GOAL_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_GOALS.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('PHASE_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_PHASES.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('WEEK_START_DATE', sa.DateTime, nullable=False),
        sa.Column('WEEK_END_DATE', sa.DateTime, nullable=False),
        sa.Column('AI_CONTEXT', JSON, nullable=True),
        sa.Column('AI_RESPONSE', JSON, nullable=True),
        sa.Column('CREATED_AT', sa.DateTime, nullable=False, server_default=sa.text('current_timestamp()')),
    )

    # SMALLSTEP_TASKS
    op.create_table(
        'SMALLSTEP_TASKS',
        sa.Column('ID', INTEGER(11), primary_key=True, autoincrement=True),
        sa.Column('WEEKLY_PLAN_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_WEEKLY_PLANS.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('GOAL_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_GOALS.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('TASK_ORDER', INTEGER(11), nullable=False),
        sa.Column('TASK_TITLE', sa.String(200), nullable=False),
        sa.Column('TASK_DESCRIPTION', LONGTEXT, nullable=True),
        sa.Column('ESTIMATED_MINUTES', INTEGER(11), nullable=True),
        sa.Column('STATUS', ENUM('LOCKED', 'AVAILABLE', 'COMPLETED', 'SKIPPED'), default='LOCKED', server_default=sa.text("'LOCKED'")),
        sa.Column('COMPLETED_AT', sa.DateTime, nullable=True),
        sa.Column('CREATED_AT', sa.DateTime, nullable=False, server_default=sa.text('current_timestamp()')),
    )

    # SMALLSTEP_ACTIVITY_LOG
    op.create_table(
        'SMALLSTEP_ACTIVITY_LOG',
        sa.Column('ID', INTEGER(11), primary_key=True, autoincrement=True),
        sa.Column('USER_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_USERS.ID', ondelete='CASCADE'), nullable=False),
        sa.Column('TASK_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_TASKS.ID', ondelete='SET NULL'), nullable=True),
        sa.Column('GOAL_ID', INTEGER(11), sa.ForeignKey('SMALLSTEP_GOALS.ID', ondelete='SET NULL'), nullable=True),
        sa.Column('ACTION', ENUM('COMPLETED', 'SKIPPED'), nullable=False),
        sa.Column('XP_EARNED', INTEGER(11), default=0, server_default=sa.text('0')),
        sa.Column('COMPLETED_AT', sa.DateTime, nullable=False, server_default=sa.text('current_timestamp()')),
    )

    # ===== 4.5 Create indexes =====
    op.create_index('ix_phases_goal_id', 'SMALLSTEP_PHASES', ['GOAL_ID'])
    op.create_index('ix_weekly_plans_goal_id', 'SMALLSTEP_WEEKLY_PLANS', ['GOAL_ID'])
    op.create_index('ix_weekly_plans_phase_id', 'SMALLSTEP_WEEKLY_PLANS', ['PHASE_ID'])
    op.create_index('ix_tasks_weekly_plan_id', 'SMALLSTEP_TASKS', ['WEEKLY_PLAN_ID'])
    op.create_index('ix_tasks_goal_id', 'SMALLSTEP_TASKS', ['GOAL_ID'])
    op.create_index('ix_activity_log_user_id', 'SMALLSTEP_ACTIVITY_LOG', ['USER_ID'])
    op.create_index('ix_activity_log_task_id', 'SMALLSTEP_ACTIVITY_LOG', ['TASK_ID'])
    op.create_index('ix_activity_log_goal_id', 'SMALLSTEP_ACTIVITY_LOG', ['GOAL_ID'])


def downgrade() -> None:
    """Downgrade schema from v2 to v1."""
    conn = op.get_bind()

    existing_cols = [row[0] for row in conn.execute(sa.text("SHOW COLUMNS FROM SMALLSTEP_USERS")).fetchall()]
    existing_goal_cols = [row[0] for row in conn.execute(sa.text("SHOW COLUMNS FROM SMALLSTEP_GOALS")).fetchall()]

    op.drop_index('ix_activity_log_goal_id', 'SMALLSTEP_ACTIVITY_LOG')
    op.drop_index('ix_activity_log_task_id', 'SMALLSTEP_ACTIVITY_LOG')
    op.drop_index('ix_activity_log_user_id', 'SMALLSTEP_ACTIVITY_LOG')
    op.drop_index('ix_tasks_goal_id', 'SMALLSTEP_TASKS')
    op.drop_index('ix_tasks_weekly_plan_id', 'SMALLSTEP_TASKS')
    op.drop_index('ix_weekly_plans_phase_id', 'SMALLSTEP_WEEKLY_PLANS')
    op.drop_index('ix_weekly_plans_goal_id', 'SMALLSTEP_WEEKLY_PLANS')
    op.drop_index('ix_phases_goal_id', 'SMALLSTEP_PHASES')

    op.drop_table('SMALLSTEP_ACTIVITY_LOG')
    op.drop_table('SMALLSTEP_TASKS')
    op.drop_table('SMALLSTEP_WEEKLY_PLANS')
    op.drop_table('SMALLSTEP_PHASES')

    goal_cols_to_add = ['CATEGORY', 'PRIORITY', 'REPEATABLE', 'MAX_PROGRESS', 'PARTICIPANTS']
    for col in goal_cols_to_add:
        if col not in existing_goal_cols:
            op.execute(f"ALTER TABLE SMALLSTEP_GOALS ADD COLUMN {col} VARCHAR(100)")

    goal_cols_to_drop = ['GOAL_TEXT', 'GOAL_TYPE', 'STATUS', 'DEADLINE_DATE', 'CURRENT_LEVEL']
    for col in goal_cols_to_drop:
        if col in existing_goal_cols:
            op.execute(f"ALTER TABLE SMALLSTEP_GOALS DROP COLUMN {col}")

    v1_users_cols = ['PHONE', 'PROFILE_IMAGE', 'LAST_LOGIN', 'IS_ACTIVE', 'PREFERRED_LANGUAGE', 'TIMEZONE']
    for col in v1_users_cols:
        if col not in existing_cols:
            col_type = 'VARCHAR(100)'
            if col in ('LAST_LOGIN',):
                col_type = 'DATETIME'
            elif col in ('IS_ACTIVE',):
                col_type = 'TINYINT(1)'
            op.execute(f"ALTER TABLE SMALLSTEP_USERS ADD COLUMN {col} {col_type}")

    users_cols_to_drop = ['LEVEL', 'CURRENT_STREAK', 'LONGEST_STREAK', 'NOTIFICATION_ENABLED', 'NOTIFICATION_TIME']
    for col in users_cols_to_drop:
        if col in existing_cols:
            op.execute(f"ALTER TABLE SMALLSTEP_USERS DROP COLUMN {col}")

    op.execute("""
        CREATE TABLE SS_CACHED_PLANS (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            USER_ID INT NOT NULL,
            PLAN_DATA JSON,
            PLAN_VECTOR VECTOR(1024),
            CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE SS_GOAL_TEMPLATES (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            TEMPLATE_NAME VARCHAR(200),
            TEMPLATE_DATA JSON,
            CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE SS_USER_PLANS (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            USER_ID INT NOT NULL,
            PLAN_DATA JSON,
            CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE SMALLSTEP_ACTIVITIES (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            USER_ID INT NOT NULL,
            ACTIVITY_TYPE VARCHAR(50),
            ACTIVITY_DATA JSON,
            CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE SMALLSTEP_GAME_DATA (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            USER_ID INT NOT NULL,
            LEVEL INT DEFAULT 1,
            XP INT DEFAULT 0,
            STREAK INT DEFAULT 0,
            UPDATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)