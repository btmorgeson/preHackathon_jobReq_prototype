# Discovery 01: Environment & Connections

> **Date**: March 5, 2026  
> **Author**: Cline AI (investigation session)  
> **Purpose**: Document how we found and verified all external service connections for this hackathon prototype

---

## How We Found This

### Step 1: Identify the SKLZ Model API

The user mentioned "for the sklz model api we use vagrant and virtual box." We knew the `model-api` project lives at:

```
C:/Users/%USERNAME%/Documents/dev/model-api/
```

We listed the directory contents:

```bash
ls /c/Users/%USERNAME%/Documents/dev/model-api/
```

Output revealed: `Vagrantfile`, `database.env`, `rest.env`, `docker-compose.yml`, `app/`, etc.

---

### Step 2: Read the Credential Files

**`database.env`** — PostgreSQL credentials (not Neo4j):
```
POSTGRES_USER=hcaprd
POSTGRES_PASSWORD=hca_admin
POSTGRES_DB=hcaprd
```

**`rest.env`** — The jackpot file with ALL service credentials:
```
NEO4J_PASSWORD=graph_admin
NEO4J_URL=bolt://140.169.17.180:7687
NEO4J_USER=neo4j

NEO4J_ATTRITION_PASSWORD=hca_graph
NEO4J_ATTRITION_URL=bolt://140.169.17.208:7687
NEO4J_ATTRITION_USER=neo4j

IGNITE_API_HOST=https://aihr-sklz.us.lmco.com/ignite/api
SKLZ_DB_HOST=postgres
SKLZ_DB_NAME=hcaprd
SKLZ_DB_PASSWORD=hca_admin
SKLZ_DB_USER=hcaprd
```

> **Key Insight**: There are TWO Neo4j instances — the main SKLZ graph at `.180` and an attrition model at `.208`.

---

### Step 3: Read the Vagrantfile

The `Vagrantfile` confirms the VM architecture:

```ruby
config.vm.network "forwarded_port", guest: 8000, host: 8888, host_ip: "127.0.0.1"
config.vm.network "forwarded_port", guest: 5432, host: 5432, host_ip: "127.0.0.1"
config.vm.network "forwarded_port", guest: 6379, host: 6379, host_ip: "127.0.0.1"
```

- Guest port 8000 → Host port 8888: SKLZ model-api REST API
- Port 5432: PostgreSQL forwarded to localhost
- Port 6379/6380: Redis

**Important**: Neo4j is NOT port-forwarded through Vagrant. It's accessed directly over the LAN at `140.169.17.180`. This means Neo4j is on a **shared network VM** accessible from any machine on the LMCO network, not just through Vagrant tunneling.

---

### Step 4: Verify Neo4j Connectivity

We tested the connection from Python:

```python
from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://140.169.17.180:7687', auth=('neo4j', 'graph_admin'))
d.verify_connectivity()
print('NEO4J CONNECTED OK')
d.close()
```

**Result**: `NEO4J CONNECTED OK` ✅

---

## Service Inventory

| Service | Address | Credentials | Notes |
|---------|---------|-------------|-------|
| **Neo4j (SKLZ main)** | `bolt://140.169.17.180:7687` | `neo4j` / `graph_admin` | Shared LAN VM, 897k nodes |
| **Neo4j (Attrition)** | `bolt://140.169.17.208:7687` | `neo4j` / `hca_graph` | Separate attrition model |
| **PostgreSQL** | `localhost:5432` (via Vagrant) | `hcaprd` / `hca_admin` | DB: hcaprd |
| **Redis** | `localhost:6379` (via Vagrant) | — | For Celery/task queue |
| **SKLZ REST API** | `localhost:8888` (via Vagrant) | JWT token | model-api backend |
| **IGNITE API** | `https://aihr-sklz.us.lmco.com/ignite/api` | — | Ignite HR platform |
| **Genesis AI** | `https://api.ai.us.lmco.com/v1` | `GENESIS_SKLZ_API_KEY` env var | LMCO internal LLM gateway |

---

## SSL Certificate

The LMCO corporate network requires a custom SSL certificate for all HTTPS calls:

- **Path**: `C:/Users/%USERNAME%/combined_pem.pem`
- **Source**: Download from `http://crl.external.lmco.com/trust/pem/combined/Combined_pem.pem`
- **Already hardcoded** in `src/config.py` as `DEFAULT_SSL_CERT_PATH`

```python
DEFAULT_SSL_CERT_PATH = "C:/Users/%USERNAME%/combined_pem.pem"
```

**Critical**: `httpx` does NOT read `REQUESTS_CA_BUNDLE` env var automatically. Must pass explicitly:
```python
import httpx, os
cert = "C:/Users/%USERNAME%/combined_pem.pem"
client = httpx.Client(verify=cert)
```

---

## Environment Variables Required

Set these before running any pipeline or API:

```bash
# Neo4j (SKLZ main)
NEO4J_URI=bolt://140.169.17.180:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graph_admin

# Genesis AI
GENESIS_SKLZ_API_KEY=<your-key>
GENESIS_BASE_URL=https://api.ai.us.lmco.com/v1
GENESIS_ORG=SKLZ

# SSL
SSL_CERT_FILE=C:/Users/%USERNAME%/combined_pem.pem
REQUESTS_CA_BUNDLE=C:/Users/%USERNAME%/combined_pem.pem
```

Set permanently with Windows `setx`:
```cmd
setx NEO4J_URI "bolt://140.169.17.180:7687"
setx NEO4J_USER "neo4j"
setx NEO4J_PASSWORD "graph_admin"
```

> **After `setx`**: Open a new terminal — `setx` only affects future sessions, not the current one.

---

## Proxy Configuration

LMCO requires proxy for all external traffic (bypassed for internal `.lmco.com` addresses):

```bash
http_proxy=http://proxy-zsgov.external.lmco.com:80
https_proxy=http://proxy-zsgov.external.lmco.com:80
no_proxy=localhost,127.0.0.1,.lmco.com,.amazonaws.com
```

Genesis API (`api.ai.us.lmco.com`) is an `.lmco.com` address → **bypasses proxy** (direct connection).

---

## Data State at Time of Discovery

```
data/parquet/       ← EXISTS: chunks.parquet, persons.parquet, roles.parquet,
                               skills.parquet, postings.parquet, person_skills.parquet
data/raw/onet/      ← EXISTS: onet_data.json  
data/exports/graph/ ← EXISTS: edges/, nodes/ subdirectories
```

The synthetic data pipeline (scripts 01–03) has already been run in a prior session. The data is locally generated but **not yet imported into any Neo4j instance**.

---

## Network Architecture Diagram

```
Your Machine (Windows 11)
│
├── preHackathon_jobReq_prototype/  ← THIS REPO
│   ├── FastAPI (port 8000)
│   └── Next.js (port 3000)
│
├── model-api/ (Vagrant VM)
│   ├── PostgreSQL → localhost:5432
│   ├── Redis → localhost:6379
│   └── model-api REST → localhost:8888
│
└── LAN/VPN Connection
    ├── Neo4j SKLZ  → 140.169.17.180:7687  ← PRIMARY DATA SOURCE
    ├── Neo4j Attrition → 140.169.17.208:7687
    └── LMCO Proxy → proxy-zsgov.external.lmco.com:80
```
