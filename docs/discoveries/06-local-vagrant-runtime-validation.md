# 06 - Local Vagrant Neo4j Runtime Validation

## Investigation Date
March 5, 2026

## Goal
Capture the verified local runtime path used on the work machine for a fresh Neo4j graph database load.

## Environment
- Host: Windows + PowerShell
- Virtualization: Vagrant + VirtualBox
- VM: Ubuntu 22.04
- Neo4j: 5.26.21

## Commands Run
```powershell
vagrant up
vagrant provision
python scripts/03_build_graph_csv.py
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
```

## Verification Checks
### VM status
```powershell
vagrant status
```
Observed: VM state `running`.

### Host endpoints
```powershell
curl.exe -I http://localhost:7474
```
Observed: HTTP 200 from Neo4j browser endpoint.

### Bolt connectivity
Validated using Python Neo4j driver against:
- URI: `bolt://localhost:7687`
- User: `neo4j`
- Password: `password12345`

### Graph counts after import
- Total nodes: `3315`
- Total relationships: `8558`
- Label counts:
  - `Person`: 500
  - `Role`: 1267
  - `Skill`: 40
  - `Chunk`: 1498
  - `Posting`: 10
- Relationship counts:
  - `HAS_ROLE`: 1267
  - `HAS_SKILL`: 5703
  - `HAS_CHUNK`: 1498
  - `REQUIRES_SKILL`: 90

## Key Findings
1. The Vagrant path is operational end-to-end and can create a fresh database from graph CSV exports.
2. Provisioning is reliable on the corporate network only with secure-first plus bounded TLS fallback behavior in the provisioner.
3. Neo4j 5.26 admin import requires positional database syntax:
   - `neo4j-admin database import full neo4j ...`

## Operational Recommendation
Use Vagrant as the default local Neo4j runtime on the work machine. Keep Docker import scripts as an alternate path for non-Vagrant environments.
