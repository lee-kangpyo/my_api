"""rename_smallstep_columns_to_snake_case

Revision ID: 6aa5de1290fe
Revises: a9bd4c354db9
Create Date: 2026-04-26 16:32:20.622141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT, JSON, ENUM


# revision identifiers, used by Alembic.
revision: str = '6aa5de1290fe'
down_revision: Union[str, Sequence[str], None] = 'a9bd4c354db9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename all SmallStep columns from UPPER_CASE to snake_case."""
    conn = op.get_bind()

    # ===== 1. Drop all foreign key constraints =====
    # We need to drop FKs before renaming columns that are part of them
    
    # Get existing FKs for each table
    def get_fks(table_name):
        result = conn.execute(sa.text(f"""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)).fetchall()
        return result
    
    # Drop FKs
    fks_to_drop = []
    for table in ['SMALLSTEP_GOALS', 'SMALLSTEP_PHASES', 'SMALLSTEP_WEEKLY_PLANS', 
                  'SMALLSTEP_TASKS', 'SMALLSTEP_ACTIVITY_LOG']:
        for fk in get_fks(table):
            fks_to_drop.append((table, fk[0]))
    
    for table, fk_name in fks_to_drop:
        op.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {fk_name}")
    
    # ===== 2. Drop indexes =====
    indexes_to_drop = [
        ('SMALLSTEP_PHASES', 'ix_phases_goal_id'),
        ('SMALLSTEP_WEEKLY_PLANS', 'ix_weekly_plans_goal_id'),
        ('SMALLSTEP_WEEKLY_PLANS', 'ix_weekly_plans_phase_id'),
        ('SMALLSTEP_TASKS', 'ix_tasks_weekly_plan_id'),
        ('SMALLSTEP_TASKS', 'ix_tasks_goal_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_user_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_task_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_goal_id'),
    ]
    
    for table, idx_name in indexes_to_drop:
        try:
            op.execute(f"DROP INDEX {idx_name} ON {table}")
        except Exception:
            pass  # Index might not exist
    
    # ===== 3. Rename columns in SMALLSTEP_USERS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_USERS
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN NAME name VARCHAR(100) NOT NULL,
        CHANGE COLUMN EMAIL email VARCHAR(100) NULL,
        CHANGE COLUMN LEVEL level INTEGER(11) DEFAULT 1,
        CHANGE COLUMN DAILY_AVAILABLE_TIME daily_available_time INTEGER(11) NULL,
        CHANGE COLUMN EXPERIENCE_POINTS experience_points INTEGER(11) DEFAULT 0,
        CHANGE COLUMN CURRENT_STREAK current_streak INTEGER(11) DEFAULT 0,
        CHANGE COLUMN LONGEST_STREAK longest_streak INTEGER(11) DEFAULT 0,
        CHANGE COLUMN NOTIFICATION_ENABLED notification_enabled TINYINT(1) DEFAULT 1,
        CHANGE COLUMN NOTIFICATION_TIME notification_time VARCHAR(10) NULL,
        CHANGE COLUMN CREATED_AT created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHANGE COLUMN UPDATED_AT updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    """)
    
    # ===== 4. Rename columns in SMALLSTEP_GOALS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_GOALS
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN USER_ID user_id INTEGER(11) NOT NULL,
        CHANGE COLUMN TITLE title VARCHAR(200) NOT NULL DEFAULT '',
        CHANGE COLUMN DESCRIPTION description LONGTEXT NULL,
        CHANGE COLUMN GOAL_TEXT goal_text LONGTEXT NOT NULL,
        CHANGE COLUMN GOAL_TYPE goal_type ENUM('DEADLINE', 'ONGOING') DEFAULT 'ONGOING',
        CHANGE COLUMN STATUS status ENUM('active', 'completed', 'paused') DEFAULT 'active',
        CHANGE COLUMN DEADLINE_DATE deadline_date DATETIME NULL,
        CHANGE COLUMN CURRENT_LEVEL current_level INTEGER(11) DEFAULT 1,
        CHANGE COLUMN CREATED_AT created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHANGE COLUMN UPDATED_AT updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    """)
    
    # ===== 5. Rename columns in SMALLSTEP_PHASES =====
    op.execute("""
        ALTER TABLE SMALLSTEP_PHASES
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN GOAL_ID goal_id INTEGER(11) NOT NULL,
        CHANGE COLUMN PHASE_ORDER phase_order INTEGER(11) NOT NULL,
        CHANGE COLUMN PHASE_TITLE phase_title VARCHAR(200) NOT NULL,
        CHANGE COLUMN PHASE_DESCRIPTION phase_description LONGTEXT NULL,
        CHANGE COLUMN ESTIMATED_WEEKS estimated_weeks INTEGER(11) NULL,
        CHANGE COLUMN STATUS status ENUM('PENDING', 'ACTIVE', 'COMPLETED') DEFAULT 'PENDING',
        CHANGE COLUMN STARTED_AT started_at DATETIME NULL,
        CHANGE COLUMN COMPLETED_AT completed_at DATETIME NULL,
        CHANGE COLUMN CREATED_AT created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 6. Rename columns in SMALLSTEP_WEEKLY_PLANS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_WEEKLY_PLANS
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN GOAL_ID goal_id INTEGER(11) NOT NULL,
        CHANGE COLUMN PHASE_ID phase_id INTEGER(11) NOT NULL,
        CHANGE COLUMN WEEK_START_DATE week_start_date DATETIME NOT NULL,
        CHANGE COLUMN WEEK_END_DATE week_end_date DATETIME NOT NULL,
        CHANGE COLUMN AI_CONTEXT ai_context JSON NULL,
        CHANGE COLUMN AI_RESPONSE ai_response JSON NULL,
        CHANGE COLUMN CREATED_AT created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 7. Rename columns in SMALLSTEP_TASKS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_TASKS
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN WEEKLY_PLAN_ID weekly_plan_id INTEGER(11) NOT NULL,
        CHANGE COLUMN GOAL_ID goal_id INTEGER(11) NOT NULL,
        CHANGE COLUMN TASK_ORDER task_order INTEGER(11) NOT NULL,
        CHANGE COLUMN TASK_TITLE task_title VARCHAR(200) NOT NULL,
        CHANGE COLUMN TASK_DESCRIPTION task_description LONGTEXT NULL,
        CHANGE COLUMN ESTIMATED_MINUTES estimated_minutes INTEGER(11) NULL,
        CHANGE COLUMN STATUS status ENUM('LOCKED', 'AVAILABLE', 'COMPLETED', 'SKIPPED') DEFAULT 'LOCKED',
        CHANGE COLUMN COMPLETED_AT completed_at DATETIME NULL,
        CHANGE COLUMN CREATED_AT created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 8. Rename columns in SMALLSTEP_ACTIVITY_LOG =====
    op.execute("""
        ALTER TABLE SMALLSTEP_ACTIVITY_LOG
        CHANGE COLUMN ID id INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN USER_ID user_id INTEGER(11) NOT NULL,
        CHANGE COLUMN TASK_ID task_id INTEGER(11) NULL,
        CHANGE COLUMN GOAL_ID goal_id INTEGER(11) NULL,
        CHANGE COLUMN ACTION action ENUM('COMPLETED', 'SKIPPED') NOT NULL,
        CHANGE COLUMN XP_EARNED xp_earned INTEGER(11) DEFAULT 0,
        CHANGE COLUMN COMPLETED_AT completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 9. Recreate foreign keys =====
    op.execute("""
        ALTER TABLE SMALLSTEP_GOALS
        ADD CONSTRAINT fk_goals_user FOREIGN KEY (user_id) REFERENCES SMALLSTEP_USERS(id) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_PHASES
        ADD CONSTRAINT fk_phases_goal FOREIGN KEY (goal_id) REFERENCES SMALLSTEP_GOALS(id) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_WEEKLY_PLANS
        ADD CONSTRAINT fk_weekly_plans_goal FOREIGN KEY (goal_id) REFERENCES SMALLSTEP_GOALS(id) ON DELETE CASCADE,
        ADD CONSTRAINT fk_weekly_plans_phase FOREIGN KEY (phase_id) REFERENCES SMALLSTEP_PHASES(id) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_TASKS
        ADD CONSTRAINT fk_tasks_weekly_plan FOREIGN KEY (weekly_plan_id) REFERENCES SMALLSTEP_WEEKLY_PLANS(id) ON DELETE CASCADE,
        ADD CONSTRAINT fk_tasks_goal FOREIGN KEY (goal_id) REFERENCES SMALLSTEP_GOALS(id) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_ACTIVITY_LOG
        ADD CONSTRAINT fk_activity_log_user FOREIGN KEY (user_id) REFERENCES SMALLSTEP_USERS(id) ON DELETE CASCADE,
        ADD CONSTRAINT fk_activity_log_task FOREIGN KEY (task_id) REFERENCES SMALLSTEP_TASKS(id) ON DELETE SET NULL,
        ADD CONSTRAINT fk_activity_log_goal FOREIGN KEY (goal_id) REFERENCES SMALLSTEP_GOALS(id) ON DELETE SET NULL
    """)
    
    # ===== 10. Recreate indexes =====
    op.execute("CREATE INDEX ix_phases_goal_id ON SMALLSTEP_PHASES(goal_id)")
    op.execute("CREATE INDEX ix_weekly_plans_goal_id ON SMALLSTEP_WEEKLY_PLANS(goal_id)")
    op.execute("CREATE INDEX ix_weekly_plans_phase_id ON SMALLSTEP_WEEKLY_PLANS(phase_id)")
    op.execute("CREATE INDEX ix_tasks_weekly_plan_id ON SMALLSTEP_TASKS(weekly_plan_id)")
    op.execute("CREATE INDEX ix_tasks_goal_id ON SMALLSTEP_TASKS(goal_id)")
    op.execute("CREATE INDEX ix_activity_log_user_id ON SMALLSTEP_ACTIVITY_LOG(user_id)")
    op.execute("CREATE INDEX ix_activity_log_task_id ON SMALLSTEP_ACTIVITY_LOG(task_id)")
    op.execute("CREATE INDEX ix_activity_log_goal_id ON SMALLSTEP_ACTIVITY_LOG(goal_id)")


def downgrade() -> None:
    """Revert column names back to UPPER_CASE."""
    conn = op.get_bind()
    
    # ===== 1. Drop all foreign key constraints =====
    def get_fks(table_name):
        result = conn.execute(sa.text(f"""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)).fetchall()
        return result
    
    fks_to_drop = []
    for table in ['SMALLSTEP_GOALS', 'SMALLSTEP_PHASES', 'SMALLSTEP_WEEKLY_PLANS', 
                  'SMALLSTEP_TASKS', 'SMALLSTEP_ACTIVITY_LOG']:
        for fk in get_fks(table):
            fks_to_drop.append((table, fk[0]))
    
    for table, fk_name in fks_to_drop:
        op.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {fk_name}")
    
    # ===== 2. Drop indexes =====
    indexes_to_drop = [
        ('SMALLSTEP_PHASES', 'ix_phases_goal_id'),
        ('SMALLSTEP_WEEKLY_PLANS', 'ix_weekly_plans_goal_id'),
        ('SMALLSTEP_WEEKLY_PLANS', 'ix_weekly_plans_phase_id'),
        ('SMALLSTEP_TASKS', 'ix_tasks_weekly_plan_id'),
        ('SMALLSTEP_TASKS', 'ix_tasks_goal_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_user_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_task_id'),
        ('SMALLSTEP_ACTIVITY_LOG', 'ix_activity_log_goal_id'),
    ]
    
    for table, idx_name in indexes_to_drop:
        try:
            op.execute(f"DROP INDEX {idx_name} ON {table}")
        except Exception:
            pass
    
    # ===== 3. Rename columns back in SMALLSTEP_USERS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_USERS
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN name NAME VARCHAR(100) NOT NULL,
        CHANGE COLUMN email EMAIL VARCHAR(100) NULL,
        CHANGE COLUMN level LEVEL INTEGER(11) DEFAULT 1,
        CHANGE COLUMN daily_available_time DAILY_AVAILABLE_TIME INTEGER(11) NULL,
        CHANGE COLUMN experience_points EXPERIENCE_POINTS INTEGER(11) DEFAULT 0,
        CHANGE COLUMN current_streak CURRENT_STREAK INTEGER(11) DEFAULT 0,
        CHANGE COLUMN longest_streak LONGEST_STREAK INTEGER(11) DEFAULT 0,
        CHANGE COLUMN notification_enabled NOTIFICATION_ENABLED TINYINT(1) DEFAULT 1,
        CHANGE COLUMN notification_time NOTIFICATION_TIME VARCHAR(10) NULL,
        CHANGE COLUMN created_at CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHANGE COLUMN updated_at UPDATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    """)
    
    # ===== 4. Rename columns back in SMALLSTEP_GOALS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_GOALS
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN user_id USER_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN title TITLE VARCHAR(200) NOT NULL DEFAULT '',
        CHANGE COLUMN description DESCRIPTION LONGTEXT NULL,
        CHANGE COLUMN goal_text GOAL_TEXT LONGTEXT NOT NULL,
        CHANGE COLUMN goal_type GOAL_TYPE ENUM('DEADLINE', 'ONGOING') DEFAULT 'ONGOING',
        CHANGE COLUMN status STATUS ENUM('active', 'completed', 'paused') DEFAULT 'active',
        CHANGE COLUMN deadline_date DEADLINE_DATE DATETIME NULL,
        CHANGE COLUMN current_level CURRENT_LEVEL INTEGER(11) DEFAULT 1,
        CHANGE COLUMN created_at CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHANGE COLUMN updated_at UPDATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    """)
    
    # ===== 5. Rename columns back in SMALLSTEP_PHASES =====
    op.execute("""
        ALTER TABLE SMALLSTEP_PHASES
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN goal_id GOAL_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN phase_order PHASE_ORDER INTEGER(11) NOT NULL,
        CHANGE COLUMN phase_title PHASE_TITLE VARCHAR(200) NOT NULL,
        CHANGE COLUMN phase_description PHASE_DESCRIPTION LONGTEXT NULL,
        CHANGE COLUMN estimated_weeks ESTIMATED_WEEKS INTEGER(11) NULL,
        CHANGE COLUMN status STATUS ENUM('PENDING', 'ACTIVE', 'COMPLETED') DEFAULT 'PENDING',
        CHANGE COLUMN started_at STARTED_AT DATETIME NULL,
        CHANGE COLUMN completed_at COMPLETED_AT DATETIME NULL,
        CHANGE COLUMN created_at CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 6. Rename columns back in SMALLSTEP_WEEKLY_PLANS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_WEEKLY_PLANS
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN goal_id GOAL_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN phase_id PHASE_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN week_start_date WEEK_START_DATE DATETIME NOT NULL,
        CHANGE COLUMN week_end_date WEEK_END_DATE DATETIME NOT NULL,
        CHANGE COLUMN ai_context AI_CONTEXT JSON NULL,
        CHANGE COLUMN ai_response AI_RESPONSE JSON NULL,
        CHANGE COLUMN created_at CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 7. Rename columns back in SMALLSTEP_TASKS =====
    op.execute("""
        ALTER TABLE SMALLSTEP_TASKS
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN weekly_plan_id WEEKLY_PLAN_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN goal_id GOAL_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN task_order TASK_ORDER INTEGER(11) NOT NULL,
        CHANGE COLUMN task_title TASK_TITLE VARCHAR(200) NOT NULL,
        CHANGE COLUMN task_description TASK_DESCRIPTION LONGTEXT NULL,
        CHANGE COLUMN estimated_minutes ESTIMATED_MINUTES INTEGER(11) NULL,
        CHANGE COLUMN status STATUS ENUM('LOCKED', 'AVAILABLE', 'COMPLETED', 'SKIPPED') DEFAULT 'LOCKED',
        CHANGE COLUMN completed_at COMPLETED_AT DATETIME NULL,
        CHANGE COLUMN created_at CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 8. Rename columns back in SMALLSTEP_ACTIVITY_LOG =====
    op.execute("""
        ALTER TABLE SMALLSTEP_ACTIVITY_LOG
        CHANGE COLUMN id ID INTEGER(11) NOT NULL AUTO_INCREMENT,
        CHANGE COLUMN user_id USER_ID INTEGER(11) NOT NULL,
        CHANGE COLUMN task_id TASK_ID INTEGER(11) NULL,
        CHANGE COLUMN goal_id GOAL_ID INTEGER(11) NULL,
        CHANGE COLUMN action ACTION ENUM('COMPLETED', 'SKIPPED') NOT NULL,
        CHANGE COLUMN xp_earned XP_EARNED INTEGER(11) DEFAULT 0,
        CHANGE COLUMN completed_at COMPLETED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    """)
    
    # ===== 9. Recreate foreign keys =====
    op.execute("""
        ALTER TABLE SMALLSTEP_GOALS
        ADD CONSTRAINT fk_goals_user FOREIGN KEY (USER_ID) REFERENCES SMALLSTEP_USERS(ID) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_PHASES
        ADD CONSTRAINT fk_phases_goal FOREIGN KEY (GOAL_ID) REFERENCES SMALLSTEP_GOALS(ID) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_WEEKLY_PLANS
        ADD CONSTRAINT fk_weekly_plans_goal FOREIGN KEY (GOAL_ID) REFERENCES SMALLSTEP_GOALS(ID) ON DELETE CASCADE,
        ADD CONSTRAINT fk_weekly_plans_phase FOREIGN KEY (PHASE_ID) REFERENCES SMALLSTEP_PHASES(ID) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_TASKS
        ADD CONSTRAINT fk_tasks_weekly_plan FOREIGN KEY (WEEKLY_PLAN_ID) REFERENCES SMALLSTEP_WEEKLY_PLANS(ID) ON DELETE CASCADE,
        ADD CONSTRAINT fk_tasks_goal FOREIGN KEY (GOAL_ID) REFERENCES SMALLSTEP_GOALS(ID) ON DELETE CASCADE
    """)
    
    op.execute("""
        ALTER TABLE SMALLSTEP_ACTIVITY_LOG
        ADD CONSTRAINT fk_activity_log_user FOREIGN KEY (USER_ID) REFERENCES SMALLSTEP_USERS(ID) ON DELETE CASCADE,
        ADD CONSTRAINT fk_activity_log_task FOREIGN KEY (TASK_ID) REFERENCES SMALLSTEP_TASKS(ID) ON DELETE SET NULL,
        ADD CONSTRAINT fk_activity_log_goal FOREIGN KEY (GOAL_ID) REFERENCES SMALLSTEP_GOALS(ID) ON DELETE SET NULL
    """)
    
    # ===== 10. Recreate indexes =====
    op.execute("CREATE INDEX ix_phases_goal_id ON SMALLSTEP_PHASES(GOAL_ID)")
    op.execute("CREATE INDEX ix_weekly_plans_goal_id ON SMALLSTEP_WEEKLY_PLANS(GOAL_ID)")
    op.execute("CREATE INDEX ix_weekly_plans_phase_id ON SMALLSTEP_WEEKLY_PLANS(PHASE_ID)")
    op.execute("CREATE INDEX ix_tasks_weekly_plan_id ON SMALLSTEP_TASKS(WEEKLY_PLAN_ID)")
    op.execute("CREATE INDEX ix_tasks_goal_id ON SMALLSTEP_TASKS(GOAL_ID)")
    op.execute("CREATE INDEX ix_activity_log_user_id ON SMALLSTEP_ACTIVITY_LOG(USER_ID)")
    op.execute("CREATE INDEX ix_activity_log_task_id ON SMALLSTEP_ACTIVITY_LOG(TASK_ID)")
    op.execute("CREATE INDEX ix_activity_log_goal_id ON SMALLSTEP_ACTIVITY_LOG(GOAL_ID)")
