from sqlalchemy import text
from app import app, db

# List your tables here
tables = [
    ("admin", "id"),
    ("user", "id"),
    ("category", "id"),
    ("recipe", "id"),
    ("blog", "id"),
    ("comment", "id"),
    ("saved_recipe", "id"),   # Change this if your table name is different
]

with app.app_context():

    print("=" * 60)
    print("Fixing PostgreSQL Sequences")
    print("=" * 60)

    for table, column in tables:

        try:

            # user is a reserved word in PostgreSQL
            table_name = f'"{table}"' if table == "user" else table

            # Get maximum id
            max_id = db.session.execute(
                text(f"SELECT COALESCE(MAX({column}), 0) FROM {table_name}")
            ).scalar()

            # Reset sequence
            db.session.execute(
                text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', '{column}'),
                        {max_id},
                        true
                    );
                """)
            )

            db.session.commit()

            print(f"✓ {table:<15} sequence set to {max_id}")

        except Exception as e:

            db.session.rollback()
            print(f"✗ {table:<15} -> {e}")

    print("\nAll sequences processed successfully!")