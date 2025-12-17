# FKG-Core

County-hosted knowledge graph runtime for community resource data.

fkg-core/
├── README.md
├── LICENSE
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   ├── fkg.example.yaml
│   └── logging.yaml
├── schemas/
│   ├── v0.1/
│   │   ├── entity.organization.json
│   │   ├── entity.service.json
│   │   ├── entity.location.json
│   │   ├── entity.person.json
│   │   ├── edge.schema.json
│   │   └── pkg.manifest.json
│   └── migrations/
├── core/
│   ├── ids/                # stable IDs, hashing, namespaces
│   ├── validate/           # schema validation
│   ├── normalize/          # name/address/phone/url normalization
│   ├── provenance/         # sources, evidence, confidence
│   ├── changelog/          # append-only event log
│   └── storage/            # DB abstraction
├── ingest/
│   ├── loaders/            # CSV/JSON/MD importers (for mrn-vault)
│   ├── parsers/            # source-specific parsers
│   └── jobs/               # scheduled pulls/refreshes
├── federation/
│   ├── remotes/            # remote registry + trust rules
│   ├── pull/               # pull snapshots, verify signatures, import
│   └── cache/              # local cached remote views
├── api/
│   ├── http/               # REST endpoints
│   ├── graph/              # query layer
│   └── openapi.yaml
├── cli/
│   ├── fkg                 # entrypoint
│   └── commands/           # init, import, export, serve, pull
├── tests/
└── docs/
    ├── COUNTY_DEPLOY.md
    ├── PKG_FORMAT.md
    └── FEDERATION.md

# The PKG (Portable Knowledge Graph) format

pkg/
├── manifest.json           # schema_version, authority, created_at
├── entities.jsonl          # each line = entity record
├── edges.jsonl             # each line = relationship record
├── sources.jsonl           # provenance sources
├── changelog.jsonl         # optional events since last snapshot
└── signatures/
    ├── manifest.sig
    └── pkg.sig


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
