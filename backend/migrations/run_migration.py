"""
Run database migrations.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db_connection

def run_migration(migration_file):
    """Run a SQL migration file"""
    print(f"Running migration: {migration_file}")

    # Read migration file
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Execute migration
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                print(f"Executing: {statement[:100]}...")
                cursor.execute(statement)

        conn.commit()
        print("[OK] Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Get migration number from command line or default to latest
    if len(sys.argv) > 1:
        migration_num = sys.argv[1]
    else:
        # Run all migrations in order
        migrations = [
            '001_create_refresh_tokens_table.sql',
            '002_add_email_verification_fields.sql'
        ]
        for migration in migrations:
            migration_file = os.path.join(os.path.dirname(__file__), migration)
            if os.path.exists(migration_file):
                run_migration(migration_file)
        sys.exit(0)

    migration_file = os.path.join(
        os.path.dirname(__file__),
        migration_num if migration_num.endswith('.sql') else f'{migration_num}.sql'
    )

    run_migration(migration_file)
