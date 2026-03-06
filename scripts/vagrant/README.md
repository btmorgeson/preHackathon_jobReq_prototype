# Vagrant Neo4j Helpers

- `provision_neo4j.sh`: installs and configures Neo4j inside the VM.
- `reset_and_import.sh`: recreates a fresh `neo4j` database from `/workspace/data/exports/graph`.

Typical flow from host:
```powershell
vagrant up
python scripts/03_build_graph_csv.py
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
```
