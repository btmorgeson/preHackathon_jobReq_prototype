#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

NEO4J_PASSWORD="${NEO4J_PASSWORD:-password12345}"
ALLOW_INSECURE_TLS_BOOTSTRAP="${ALLOW_INSECURE_TLS_BOOTSTRAP:-true}"
NEO4J_CONF="/etc/neo4j/neo4j.conf"
NEO4J_KEYRING="/etc/apt/keyrings/neo4j.gpg"

set_conf() {
  local key="$1"
  local value="$2"
  if grep -qE "^#?${key}=" "$NEO4J_CONF"; then
    sed -i "s|^#\?${key}=.*|${key}=${value}|g" "$NEO4J_CONF"
  else
    echo "${key}=${value}" >>"$NEO4J_CONF"
  fi
}

echo "Installing base dependencies..."
rm -f /etc/apt/sources.list.d/neo4j.list
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release apt-transport-https

echo "Configuring Neo4j apt repository..."
install -m 0755 -d /etc/apt/keyrings
if [[ ! -s "$NEO4J_KEYRING" ]] || ! gpg --show-keys "$NEO4J_KEYRING" >/dev/null 2>&1; then
  if curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key -o /tmp/neo4j.key; then
    echo "Downloaded Neo4j key with standard TLS verification."
  elif [[ "$ALLOW_INSECURE_TLS_BOOTSTRAP" == "true" ]]; then
    echo "Standard TLS fetch failed; retrying Neo4j key download with insecure TLS fallback."
    curl -kfsSL https://debian.neo4j.com/neotechnology.gpg.key -o /tmp/neo4j.key
  else
    echo "Failed to download Neo4j key with TLS verification and insecure fallback is disabled."
    exit 1
  fi
  if ! grep -q "BEGIN PGP PUBLIC KEY BLOCK" /tmp/neo4j.key; then
    echo "Neo4j key download did not return a valid armored key."
    exit 1
  fi
  gpg --dearmor --yes -o "$NEO4J_KEYRING" /tmp/neo4j.key
  rm -f /tmp/neo4j.key
fi
echo "deb [signed-by=${NEO4J_KEYRING}] https://debian.neo4j.com stable 5" >/etc/apt/sources.list.d/neo4j.list

if [[ "$ALLOW_INSECURE_TLS_BOOTSTRAP" == "true" ]]; then
  cat >/etc/apt/apt.conf.d/99neo4j-insecure-tls <<'EOF'
Acquire::https::debian.neo4j.com::Verify-Peer "false";
Acquire::https::debian.neo4j.com::Verify-Host "false";
EOF
fi

apt-get update -y
if ! dpkg -s neo4j >/dev/null 2>&1; then
  apt-get install -y neo4j
fi

echo "Configuring Neo4j listen addresses..."
set_conf "server.default_listen_address" "0.0.0.0"
set_conf "server.http.listen_address" "0.0.0.0:7474"
set_conf "server.bolt.listen_address" "0.0.0.0:7687"

echo "Setting initial Neo4j password if needed..."
if [[ ! -f /var/lib/neo4j/data/dbms/auth ]]; then
  neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD"
fi

echo "Starting Neo4j service..."
systemctl daemon-reload
systemctl enable neo4j
systemctl restart neo4j

echo "Waiting for Neo4j HTTP endpoint..."
for _ in $(seq 1 60); do
  if curl -sSf http://localhost:7474 >/dev/null; then
    echo "Neo4j provisioned and reachable."
    exit 0
  fi
  sleep 2
done

echo "Neo4j did not become healthy in time."
systemctl status neo4j --no-pager || true
exit 1
