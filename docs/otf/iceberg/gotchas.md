# Iceberg Gotchas

- Small-file accumulation can make planning and metadata operations expensive.
- Catalog endpoint, warehouse URI, and S3 credentials must align across REST server and engine clients.
- Object storage path-style access settings are required for many local MinIO setups.
- Incompatible engine/runtime versions can break procedure support or metadata table access.
- Treat table metadata directory as managed state; avoid manual edits.
