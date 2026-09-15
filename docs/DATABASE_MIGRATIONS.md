# Database Migrations

AeroRecon uses [Alembic](https://alembic.sqlalchemy.org/) to manage database schema migrations for both SQLite and PostgreSQL.

## Fresh Installation

For a fresh deployment where the database does not exist:
1. Ensure the `DATABASE_URL` environment variable is set (or let it default to the local SQLite database).
2. Run Alembic upgrade to create the schema:
   ```bash
   alembic upgrade head
   ```

## Upgrading an Existing Installation

If you already have an existing database (e.g., SQLite `data/jobs.db`) created by older versions of AeroRecon using `Base.metadata.create_all()`:

1. **Do not** run `alembic upgrade head` immediately as the table already exists.
2. Tell Alembic to consider the current state as already synchronized with the initial schema baseline by running:
   ```bash
   alembic stamp head
   ```
3. For future updates, you can safely run `alembic upgrade head` to apply new migrations.

## Downgrade / Rollback Procedure

If you need to roll back the most recent migration:
```bash
alembic downgrade -1
```

Or to a specific revision ID:
```bash
alembic downgrade <revision_id>
```

## SQLite Workflow

By default, the application uses an SQLite database located at `data/jobs.db`.
- Alembic is configured to use `render_as_batch=True` to support ALTER TABLE operations that are natively limited in SQLite.
- Run `alembic upgrade head` (or `stamp` if upgrading an existing installation) in the environment where the app runs.

## PostgreSQL Workflow

If `DATABASE_URL` points to a PostgreSQL database (e.g., `postgresql://user:pass@localhost:5432/aerorecon`):
- Ensure `psycopg2-binary` or `asyncpg` is installed (as needed by your SQLAlchemy engine URL).
- The migration commands (`alembic upgrade head`, `alembic stamp head`) work the same way. Alembic automatically handles PostgreSQL's dialect-specific types and syntax.

> **Note:** The `app.db.init_db()` function has been retained for backwards compatibility, but it will not destructively overwrite existing tables managed by Alembic. In production, prefer running `alembic upgrade head` before starting the application over relying on `create_all()`.
