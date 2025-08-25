from .db import get_postgres_connection



def create_update_last_updated_function():
    """Create the update_last_updated function if it doesn't exist"""
    conn = get_postgres_connection("update_function")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_last_updated()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_updated = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
        conn.commit()
        print("update_last_updated function created or updated")
    except Exception as e:
        print(f"Error creating function: {e}")
        raise
    finally:
        conn.close()

def users_table():
    """Create users table if it doesn't exist"""
    conn = get_postgres_connection("users")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    first_name TEXT,
                    timezone TEXT DEFAULT 'UTC',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Users table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()


def user_summaries():
    """Create user summaries table if it doesn't exist"""
    conn = get_postgres_connection("user_summaries")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_summaries (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    summary TEXT NOT NULL,
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("User summaries table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()

# Trigger for last_updated in user_summaries
def user_summaries_trigger():
    """Create trigger for last_updated in user_summaries"""
    conn = get_postgres_connection("user_summaries")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TRIGGER user_summaries_trigger
                BEFORE UPDATE ON user_summaries
                FOR EACH ROW
                EXECUTE FUNCTION update_last_updated();
            """)
        conn.commit()
        print("User summaries trigger created or already exists")
    except Exception as e:
        print(f"Error creating trigger: {e}")
        raise
    finally:
        conn.close()    

def goals_table():
    """Create goals table if it doesn't exist"""
    conn = get_postgres_connection("goals")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT,
                    status VARCHAR DEFAULT 'active',
                    start_date DATE,
                    target_date DATE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Goals table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()


# trigger for last_updated in goals
def goals_trigger():
    """Create trigger for last_updated in goals"""
    conn = get_postgres_connection("goals")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TRIGGER goals_trigger
                BEFORE UPDATE ON goals
                FOR EACH ROW
                EXECUTE FUNCTION update_last_updated();
            """)
        conn.commit()
        print("Goals trigger created or already exists")
    except Exception as e:
        print(f"Error creating trigger: {e}")
        raise
    finally:
        conn.close()

def milestones_table():
    """Create milestones table if it doesn't exist"""
    conn = get_postgres_connection("milestones")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    milestone_id BIGSERIAL PRIMARY KEY,
                    goal_id BIGINT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
                    description TEXT NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    target_date DATE,
                    completed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Milestones table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()

# trigger for last_updated in milestones
def milestones_trigger():
    """Create trigger for last_updated in milestones"""
    conn = get_postgres_connection("milestones")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TRIGGER milestones_trigger
                BEFORE UPDATE ON milestones
                FOR EACH ROW
                EXECUTE FUNCTION update_last_updated();
            """)
        conn.commit()
        print("Milestones trigger created or already exists")
    except Exception as e:
        print(f"Error creating trigger: {e}")
        raise
    finally:
        conn.close()


def habits_table():
    """Create habits table if it doesn't exist"""
    conn = get_postgres_connection("habits")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    habit_id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    description TEXT NOT NULL,
                    frequency_type VARCHAR NOT NULL,
                    frequency_value INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Habits table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()

# trigger for last_updated in habits
def habits_trigger():
    """Create trigger for last_updated in habits"""
    conn = get_postgres_connection("habits")
    try:
        with conn.cursor() as cur:
            cur.execute(""" 
                CREATE TRIGGER habits_trigger
                BEFORE UPDATE ON habits
                FOR EACH ROW
                EXECUTE FUNCTION update_last_updated();
            """)
        conn.commit()
        print("Habits trigger created or already exists")
    except Exception as e:
        print(f"Error creating trigger: {e}")
        raise
    finally:
        conn.close()


def  progress_logs_table():
    """Create progress logs table if it doesn't exist"""
    conn = get_postgres_connection("progress_logs")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS progress_logs (
                    log_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    related_goal_id BIGINT REFERENCES goals(goal_id) ON DELETE SET NULL,
                    related_habit_id BIGINT REFERENCES habits(habit_id) ON DELETE SET NULL,
                    log_type VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Progress logs table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()

# trigger for last_updated in progress_logs
def progress_logs_trigger():
    """Create trigger for last_updated in progress_logs"""
    conn = get_postgres_connection("progress_logs")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TRIGGER progress_logs_trigger
                BEFORE UPDATE ON progress_logs
                FOR EACH ROW
                EXECUTE FUNCTION update_last_updated();
            """)
        conn.commit()
        print("Progress logs trigger created or already exists")
    except Exception as e:
        print(f"Error creating trigger: {e}")
        raise
    finally:
        conn.close()

#Table to store all users conversations
def conversations_table():
    """Create conversations table if it doesn't exist"""
    conn = get_postgres_connection("conversations")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    conversation_type VARCHAR NOT NULL,
                    conversation_data JSONB,
                    state JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
        print("Conversations table created or already exists")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise
    finally:
        conn.close()

def create_indexes():
    """Create performance indexes for better query performance"""
    conn = get_postgres_connection("indexes")
    try:
        with conn.cursor() as cur:
            # Indexes for goals table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals(target_date);")
            
            # Indexes for milestones table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_milestones_goal_id ON milestones(goal_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);")
            
            # Indexes for habits table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id);")
            
            # Indexes for progress_logs table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_progress_logs_user_id ON progress_logs(user_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_progress_logs_created_at ON progress_logs(created_at);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_progress_logs_goal_id ON progress_logs(related_goal_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_progress_logs_habit_id ON progress_logs(related_habit_id);")
            
            # Indexes for conversations table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);")
            
        conn.commit()
        print("Performance indexes created or already exist")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        raise
    finally:
        conn.close()

def create_all_tables():
    """Create all tables and functions for GoalGetter"""
    print("Setting up GoalGetter database...")
    
    # Create the update function
    create_update_last_updated_function()
    
    # Create all tables
    users_table()
    user_summaries()
    goals_table()
    milestones_table()
    habits_table()
    progress_logs_table()
    conversations_table()
    
    # Create triggers
    user_summaries_trigger()
    goals_trigger()
    milestones_trigger()
    habits_trigger()
    progress_logs_trigger()
    
    # Create performance indexes
    create_indexes()
    
    print("✅ GoalGetter database setup complete!")

if __name__ == "__main__":
    create_all_tables()






