# County Deployment Guide

This guide covers deploying FKG-Core in a county environment.

## Prerequisites

- Docker and Docker Compose (recommended) OR Python 3.12+
- PostgreSQL 16+
- Network access for federation (optional)

## Deployment Options

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/fkg-core.git
   cd fkg-core
   ```

2. Create your configuration:
   ```bash
   cp config/fkg.example.yaml config/fkg.yaml
   ```

3. Edit `config/fkg.yaml` with your county's details:
   ```yaml
   instance:
     id: your-county.state.us
     authority_name: Your County Resource Network
     jurisdiction: Your County, State
   ```

4. Start the services:
   ```bash
   cd docker
   docker compose up -d
   ```

5. Initialize the database:
   ```bash
   docker compose exec api fkg db init
   ```

6. Verify deployment:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/whoami
   ```

### Option 2: Native Installation

1. Install Python 3.12+ and PostgreSQL 16+

2. Clone and install:
   ```bash
   git clone https://github.com/your-org/fkg-core.git
   cd fkg-core
   pip install -e .
   ```

3. Set up PostgreSQL:
   ```sql
   CREATE USER fkg WITH PASSWORD 'your-secure-password';
   CREATE DATABASE fkg OWNER fkg;
   ```

4. Configure environment:
   ```bash
   export FKG_DATABASE__URL="postgresql+psycopg://fkg:password@localhost:5432/fkg"
   export FKG_INSTANCE__ID="your-county.state.us"
   export FKG_INSTANCE__AUTHORITY_NAME="Your County Resource Network"
   ```

5. Initialize and run:
   ```bash
   fkg db init
   fkg serve --host 0.0.0.0 --port 8000
   ```

## Configuration Reference

### Instance Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `instance.id` | Unique identifier (domain-style) | `mrn.marin.ca.us` |
| `instance.authority_name` | Display name | `Marin Resource Network` |
| `instance.jurisdiction` | Geographic area | `Marin County, CA` |
| `instance.schema_version` | Active schema version | `v0.1` |

### Database Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `database.url` | PostgreSQL connection string | `postgresql+psycopg://user:pass@host:5432/db` |

### API Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `api.host` | Bind address | `127.0.0.1` |
| `api.port` | Port number | `8000` |
| `api.cors_enabled` | Enable CORS | `false` |

## Initial Data Load

### From CSV

```bash
fkg ingest csv --path organizations.csv --entity-type organization
```

CSV should have headers matching entity fields. At minimum, include `name`.

### From JSONL

```bash
fkg ingest jsonl --path data.jsonl
```

Each line should be a valid entity or edge JSON object.

### From Another FKG Instance

```bash
# Add remote
fkg remote add --id source-county.state.us --endpoint https://fkg.source-county.state.us

# Pull data
fkg pull --id source-county.state.us
```

## Production Considerations

### Security

1. **Database**: Use strong passwords, restrict network access
2. **API**: Run behind a reverse proxy (nginx/traefik) with TLS
3. **Network**: Use firewall rules to limit access

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 443 ssl;
    server_name fkg.your-county.state.us;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Backup

Regular PostgreSQL backups:
```bash
pg_dump -U fkg fkg > fkg_backup_$(date +%Y%m%d).sql
```

Or use PKG export:
```bash
fkg pkg export --out /backups/pkg-$(date +%Y%m%d)/
```

### Monitoring

- Monitor `/health` endpoint
- Track database size and query performance
- Log aggregation for audit trail

## Federation Setup

To enable federation with other counties:

1. Add trusted remotes to config:
   ```yaml
   federation:
     remotes:
       - id: neighbor-county.state.us
         endpoint: https://fkg.neighbor-county.state.us
         trust:
           verify_signatures: false
           allow_entity_types:
             - organization
             - service
             - location
   ```

2. Pull from remotes:
   ```bash
   fkg pull --id neighbor-county.state.us
   ```

3. Remote data is stored with the remote's authority_id, keeping it separate from local data.

## Troubleshooting

### Database Connection Issues

Check connection string and ensure PostgreSQL is running:
```bash
psql -U fkg -h localhost -d fkg
```

### Migration Errors

Run migrations manually:
```bash
alembic upgrade head
```

### API Not Starting

Check logs and verify configuration:
```bash
fkg whoami  # Test configuration loading
```

## Support

- File issues at: https://github.com/your-org/fkg-core/issues
- Community discussions: [link]
