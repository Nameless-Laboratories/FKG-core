# PKG Format Specification (v0.1)

PKG (Portable Knowledge Graph) is a format for exchanging knowledge graph data between FKG instances.

## Overview

A PKG is a directory containing:
- `manifest.json` - Metadata and checksums
- `entities.jsonl` - Entity records (one per line)
- `edges.jsonl` - Relationship records (one per line)
- `sources.jsonl` - Provenance source records
- `changelog.jsonl` - Change events (optional)
- `signatures/` - Detached signatures (v0.1 stub)

## Manifest

The manifest file contains metadata about the PKG:

```json
{
  "version": "0.1",
  "authority_id": "mrn.marin.ca.us",
  "authority_name": "Marin Resource Network",
  "jurisdiction": "Marin County, CA",
  "created_at": "2024-01-15T10:30:00Z",
  "schema_version": "v0.1",
  "counts": {
    "entities": 1500,
    "edges": 3200,
    "sources": 25
  },
  "files": {
    "entities": "entities.jsonl",
    "edges": "edges.jsonl",
    "sources": "sources.jsonl",
    "changelog": "changelog.jsonl"
  },
  "checksums": {
    "entities.jsonl": "sha256:abc123...",
    "edges.jsonl": "sha256:def456...",
    "sources.jsonl": "sha256:789ghi..."
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | PKG format version (currently "0.1") |
| `authority_id` | string | Unique identifier of the source authority |
| `authority_name` | string | Human-readable name |
| `created_at` | string | ISO 8601 timestamp |
| `schema_version` | string | Schema version for entities/edges |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `jurisdiction` | string | Geographic area |
| `counts` | object | Record counts |
| `files` | object | File paths within PKG |
| `checksums` | object | SHA256 checksums |
| `signature` | object | Signature information |

## Entities File

`entities.jsonl` contains one entity per line in JSON format:

```jsonl
{"id":"mrn.marin.ca.us:organization:abc123","type":"organization","schema_version":"v0.1","authority_id":"mrn.marin.ca.us","name":"Food Bank","description":"..."}
{"id":"mrn.marin.ca.us:service:def456","type":"service","schema_version":"v0.1","authority_id":"mrn.marin.ca.us","name":"Food Pantry","category":"food"}
```

### Entity Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique entity ID |
| `type` | string | Yes | Entity type (organization, service, etc.) |
| `schema_version` | string | Yes | Schema version |
| `authority_id` | string | Yes | Source authority |
| `name` | string | Yes | Display name |

Additional fields depend on entity type - see JSON schemas.

## Edges File

`edges.jsonl` contains one edge per line:

```jsonl
{"id":"mrn.marin.ca.us:edge:xyz789","type":"ORG_OFFERS_SERVICE","src_id":"mrn.marin.ca.us:organization:abc123","dst_id":"mrn.marin.ca.us:service:def456","schema_version":"v0.1","authority_id":"mrn.marin.ca.us","properties":{}}
```

### Edge Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique edge ID |
| `type` | string | Yes | Relationship type |
| `src_id` | string | Yes | Source entity ID |
| `dst_id` | string | Yes | Destination entity ID |
| `schema_version` | string | Yes | Schema version |
| `authority_id` | string | Yes | Source authority |
| `properties` | object | No | Additional edge properties |

### Edge Types (v0.1)

- `ORG_OFFERS_SERVICE` - Organization provides a service
- `ORG_HAS_LOCATION` - Organization has a physical location
- `SERVICE_AT_LOCATION` - Service available at location
- `PERSON_WORKS_AT_ORG` - Person employed by organization
- `PERSON_MANAGES_SERVICE` - Person manages a service
- `ORG_PARTNERS_WITH` - Organizations collaborate
- `SERVICE_REQUIRES_SERVICE` - Service dependency
- `LOCATION_NEAR_LOCATION` - Geographic proximity

## Sources File

`sources.jsonl` contains provenance sources:

```jsonl
{"id":"source:211:2024","name":"211 Database","type":"api","url":"https://api.211.org","fetched_at":"2024-01-10T00:00:00Z"}
{"id":"source:manual:2024-01","name":"Manual Entry January 2024","type":"manual"}
```

### Source Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique source ID |
| `name` | string | Yes | Display name |
| `type` | string | No | Source type (api, file, manual, etc.) |
| `url` | string | No | Source URL if applicable |
| `fetched_at` | string | No | When data was retrieved |
| `license` | string | No | Data license |

## Changelog File

Optional `changelog.jsonl` for audit trail:

```jsonl
{"seq":1,"event_type":"create_entity","authority_id":"mrn.marin.ca.us","payload":{"entity_id":"mrn.marin.ca.us:organization:abc123"},"created_at":"2024-01-15T10:00:00Z"}
{"seq":2,"event_type":"create_edge","authority_id":"mrn.marin.ca.us","payload":{"edge_id":"mrn.marin.ca.us:edge:xyz789"},"created_at":"2024-01-15T10:01:00Z"}
```

### Event Types

- `create_entity` - New entity added
- `update_entity` - Entity modified
- `delete_entity` - Entity removed
- `create_edge` - New edge added
- `update_edge` - Edge modified
- `delete_edge` - Edge removed

## Signatures (v0.1 Stub)

The `signatures/` directory is reserved for cryptographic signatures. In v0.1, signature verification is optional and uses placeholder implementation.

Future versions will support Ed25519 signatures for:
- Manifest authenticity
- Authority verification
- Data integrity

## ID Format

Entity and edge IDs follow the pattern:

```
{namespace}:{type}:{hash}
```

- `namespace`: Authority identifier (e.g., `mrn.marin.ca.us`)
- `type`: Entity type or "edge"
- `hash`: 16-character truncated SHA256

Example: `mrn.marin.ca.us:organization:a1b2c3d4e5f6g7h8`

IDs are deterministic - the same content produces the same ID.

## Validation

Before importing a PKG:

1. Verify manifest schema
2. Check file checksums
3. Validate each entity against its schema
4. Validate each edge against edge schema
5. (Future) Verify signatures

Use CLI validation:
```bash
fkg pkg validate --path ./pkg/
```

## Import Behavior

When importing a PKG:

1. **Local authority**: Entities/edges assigned to local instance ID
2. **Remote authority**: Entities/edges keep remote's authority ID

Local authority always wins - remote imports never overwrite local authoritative data.
