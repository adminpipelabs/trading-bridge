# Database Migrations

This directory contains Alembic database migrations for the Trading Bridge application.

## Setup

Migrations are automatically configured when Alembic is installed. The configuration is in `alembic.ini` and `migrations/env.py`.

## Usage

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration (manual)
alembic revision -m "Description of changes"
```

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific revision
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Check migration status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Running Migrations in Production

### Railway Deployment

Migrations should run automatically during deployment. Add to your startup script:

```bash
# Run migrations before starting the app
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Or add to `Dockerfile`:

```dockerfile
# Run migrations
RUN alembic upgrade head

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Manual Migration

If needed, run migrations manually:

```bash
export DATABASE_URL="your_database_url"
alembic upgrade head
```

## Migration Best Practices

1. **Always review auto-generated migrations** - Alembic can miss some changes
2. **Test migrations on staging first** - Never run untested migrations on production
3. **Backup database before migrations** - Use backup scripts before major schema changes
4. **Keep migrations small** - One logical change per migration
5. **Never edit existing migrations** - Create new migrations to fix issues

## Current Schema

The database includes the following tables:
- `clients` - Client information
- `wallets` - Wallet addresses
- `connectors` - Exchange connectors
- `bots` - Bot definitions
- `bot_wallets` - Encrypted bot trading wallets
- `bot_trades` - Trade history

See `app/database.py` for model definitions.
