from app.db.database import engine, Base
from sqlalchemy import text
from app.models import user


def init_db():
    # create any missing tables
    Base.metadata.create_all(bind=engine)

    # ensure new columns exist for soft-delete
    with engine.connect() as conn:
        # add is_deleted column if not present
        conn.execute(text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false;
            """
        ))
        # add deleted_at timestamp column if not present
        conn.execute(text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS deleted_at timestamp;
            """
        ))
        conn.commit()
