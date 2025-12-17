# Federation Guide

Federation enables read-only data sharing between FKG instances. A county can pull data from neighboring counties to provide a broader view of available resources.

## Concepts

### Authority

Each FKG instance is an **authority** for its own data. The authority is identified by the `instance.id` setting (e.g., `mrn.marin.ca.us`).

### Namespacing

When data is imported from a remote, it retains the remote's `authority_id`. This ensures:
- Local and remote data are clearly distinguished
- No ID collisions between authorities
- Local authoritative data is never overwritten

### Trust Model

Federation is **read-only** and **opt-in**:
- You choose which remotes to trust
- You control which entity types to accept
- Remote data supplements but never replaces local data

## Configuration

### Adding Remotes

Add trusted remotes to your `fkg.yaml`:

```yaml
federation:
  remotes:
    - id: sonoma.ca.us
      endpoint: https://fkg.sonoma.ca.us
      public_key: null  # Optional in v0.1
      trust:
        verify_signatures: false  # v0.1 default
        allow_entity_types:
          - organization
          - service
          - location
```

### Trust Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `verify_signatures` | Require valid PKG signatures | `false` |
| `allow_entity_types` | Entity types to import | All types |

## CLI Usage

### List Remotes

```bash
fkg remote list
```

### Add Remote (Interactive)

```bash
fkg remote add --id neighbor.county.us --endpoint https://fkg.neighbor.county.us
```

Note: This shows the YAML to add. Edit `fkg.yaml` manually to persist.

### Pull from Remote

```bash
fkg pull --id sonoma.ca.us
```

This will:
1. Download the remote's latest PKG
2. Verify checksums
3. Import with the remote's authority_id
4. Log events to changelog

## API Integration

### Remote Data in Queries

Queried entities include their `authority_id`, so clients can identify data source:

```json
{
  "id": "sonoma.ca.us:organization:abc123",
  "type": "organization",
  "authority_id": "sonoma.ca.us",
  "data": { "name": "Sonoma Food Bank" }
}
```

### Filtering by Authority

```bash
GET /entities?authority_id=sonoma.ca.us
```

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Marin County FKG  │     │  Sonoma County FKG  │
│   (mrn.marin.ca.us) │     │   (sonoma.ca.us)    │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │ Local Data    │  │     │  │ Local Data    │  │
│  │ authority_id: │  │     │  │ authority_id: │  │
│  │ mrn.marin...  │  │     │  │ sonoma.ca.us  │  │
│  └───────────────┘  │     │  └───────────────┘  │
│                     │     │                     │
│  ┌───────────────┐  │     │                     │
│  │ Sonoma Data   │◄─┼─────┼── GET /pkg/latest   │
│  │ authority_id: │  │     │                     │
│  │ sonoma.ca.us  │  │     │                     │
│  └───────────────┘  │     │                     │
└─────────────────────┘     └─────────────────────┘
```

## Pull Process

1. **Fetch PKG**: Download zip from `{endpoint}/pkg/latest`
2. **Extract**: Unzip to temporary directory
3. **Verify Checksums**: Compare file hashes to manifest
4. **Verify Signature**: (v0.1 stub - optional)
5. **Filter Types**: Only import allowed entity types
6. **Import**: Upsert entities/edges with remote authority_id
7. **Log Events**: Record import in changelog

## Best Practices

### Choose Trusted Partners

Only federate with authorities you trust:
- Government agencies
- Established nonprofits
- Regional collaboratives

### Regular Pulls

Schedule regular pulls to stay current:

```bash
# Example cron job (daily at 2 AM)
0 2 * * * cd /opt/fkg && fkg pull --id sonoma.ca.us
```

### Monitor Imports

Review changelog for federation activity:

```sql
SELECT * FROM events
WHERE event_type LIKE '%_entity'
  AND authority_id != 'your.local.id'
ORDER BY created_at DESC;
```

### Handle Conflicts

If the same real-world entity exists in multiple authorities:
- Each maintains its own record
- API returns all versions
- UI should handle deduplication/display

## Limitations (v0.1)

- **No push**: Data flows one-way via pull
- **No real-time**: Pull is manual or scheduled
- **Stub signatures**: Cryptographic verification not implemented
- **No diff sync**: Each pull reimports full PKG

## Future Roadmap

- Ed25519 signature verification
- Incremental sync via changelog
- Entity deduplication hints
- Trust federation (transitive remotes)
