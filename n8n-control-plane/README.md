# n8n-control-plane

Self-hosted n8n (Community Edition) with Postgres using Docker Compose.

## Setup
1. Copy env template and edit values.
```bash
cp .env.example .env
```
2. Start services.
```bash
docker compose up -d
```
3. Open n8n at `http://localhost:5678` (or your configured host).

## Start / Stop
Start:
```bash
docker compose up -d
```
Stop:
```bash
docker compose down
```

## Reset (wipe data)
This removes all persisted data volumes.
```bash
docker compose down -v
```

## Backup
Postgres (workflows, credentials, executions):
```bash
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

n8n data volume (optional):
```bash
docker compose run --rm -T n8n sh -c 'tar -czf - /home/node/.n8n' > n8n_data.tar.gz
```

## Restore
Stop the stack first:
```bash
docker compose down
```

Restore Postgres:
```bash
cat backup.sql | docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

Restore n8n data volume (optional):
```bash
cat n8n_data.tar.gz | docker compose run --rm -T n8n sh -c 'tar -xzf - -C /'
```

Start again:
```bash
docker compose up -d
```

## Notes
- Keep `.env` private (do not commit). It contains credentials and the encryption key.
- Use a strong `N8N_ENCRYPTION_KEY` and keep it stable across restarts.
