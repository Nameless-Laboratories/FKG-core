# FKG-Core

County-hosted knowledge graph runtime for community resource data.

## Features

- **Schema-first**: Entities and edges validated against versioned JSON Schemas
- **Stable IDs**: Deterministic content-addressed identifiers
- **Provenance-first**: Every entity links to source/evidence records
- **Read-only API**: HTTP API for querying the graph
- **PKG Format**: Portable Knowledge Graph snapshots with signatures
- **Federation**: Read-only pull from trusted remotes

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker (optional, for local dev)

### Using Docker

```bash
# Start Postgres and API
docker compose up

# In another terminal, initialize the database
docker compose exec api fkg db init
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Set up environment
export FKG_DATABASE__URL="postgresql+psycopg://fkg:fkg@localhost:5432/fkg"

# Initialize database
fkg db init

# Run API server
fkg serve
```

## CLI Commands

### Core
- `fkg db init` - Create/migrate database
- `fkg serve` - Run API server
- `fkg whoami` - Print instance identity

### PKG Operations
- `fkg pkg export --out ./pkg/` - Export PKG snapshot
- `fkg pkg import --path ./pkg/` - Import PKG snapshot
- `fkg pkg validate --path ./pkg/` - Validate PKG

### Data Ingestion
- `fkg ingest csv --path data.csv --entity-type organization`
- `fkg ingest jsonl --path data.jsonl`
- `fkg ingest markdown --path ./notes/` (placeholder)

### Federation
- `fkg remote add --id sonoma.ca.us --endpoint https://... --pubkey ed25519:...`
- `fkg pull --id sonoma.ca.us` - Pull remote PKG

## API Endpoints

- `GET /health` - Health check
- `GET /whoami` - Instance identity
- `GET /entities` - List entities (with query, type, limit, offset)
- `GET /entities/{id}` - Get entity by ID
- `GET /entities/{id}/neighbors` - Get connected entities
- `GET /entities/{id}/provenance` - Get provenance info
- `GET /edges` - List edges
- `GET /edges/{id}` - Get edge by ID
- `GET /sources/{id}` - Get source by ID
- `GET /pkg/latest` - Download latest PKG snapshot

## Configuration

See `config/fkg.example.yaml` for configuration options.

## License

Apache 2.0
