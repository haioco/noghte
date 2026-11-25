#!/usr/bin/env bash
# Single-node Phase 0 Point DNS service (PowerDNS Authoritative + dnsdist + PostgreSQL).
# Adapted from point-handbook_v4.html, section "پیکربندی موتور DNS" (Part 3, rev 2).
# Differences from the two-site Kubernetes design are documented in README.md.
set -euo pipefail

ZONE="${ZONE:-probe.noghte-dns.example.}"
PUBLIC_IP="${PUBLIC_IP:-$(curl -fsS --noproxy '*' https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')}"
SECRETS_FILE=/etc/noghte-dns/secrets.env
PDNS_CONF=/etc/powerdns/pdns.conf
API_CONF_DIR=/etc/powerdns-api
DNSDIST_CONF=/etc/dnsdist/dnsdist.conf

log() { echo "[install-point-dns] $*"; }

if [[ $EUID -ne 0 ]]; then echo "Run as root" >&2; exit 1; fi

export DEBIAN_FRONTEND=noninteractive
log "Installing packages"
apt-get update -qq
apt-get install -y -qq postgresql pdns-server pdns-backend-pgsql dnsdist dnsutils curl jq >/dev/null

systemctl enable --now postgresql
for _ in $(seq 1 30); do
  su postgres -c 'pg_isready -q' && break
  sleep 1
done
su postgres -c 'pg_isready' >/dev/null

# Secrets are generated on the host and never stored in the repository.
mkdir -p /etc/noghte-dns
if [[ ! -f "$SECRETS_FILE" ]]; then
  umask 077
  {
    echo "PDNS_DB_RW_PASSWORD=$(openssl rand -hex 24)"
    echo "PDNS_DB_RO_PASSWORD=$(openssl rand -hex 24)"
    echo "PDNS_API_KEY=$(openssl rand -hex 32)"
    echo "DNSDIST_WEB_PASSWORD=$(openssl rand -hex 24)"
    echo "DNSDIST_API_KEY=$(openssl rand -hex 32)"
  } > "$SECRETS_FILE"
  chmod 600 "$SECRETS_FILE"
fi
# shellcheck disable=SC1090
source "$SECRETS_FILE"

log "Preparing PostgreSQL (pdns database, rw/ro roles)"
if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='pdns_rw'\"" | grep -q 1; then
  su postgres -c "psql -c \"CREATE ROLE pdns_rw LOGIN PASSWORD '$PDNS_DB_RW_PASSWORD'\""
fi
if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='pdns_ro'\"" | grep -q 1; then
  su postgres -c "psql -c \"CREATE ROLE pdns_ro LOGIN PASSWORD '$PDNS_DB_RO_PASSWORD'\""
fi
su postgres -c "psql -c \"ALTER ROLE pdns_rw WITH LOGIN PASSWORD '$PDNS_DB_RW_PASSWORD'\""
su postgres -c "psql -c \"ALTER ROLE pdns_ro WITH LOGIN PASSWORD '$PDNS_DB_RO_PASSWORD'\""
su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='pdns'\"" | grep -q 1 || su postgres -c "createdb -O pdns_rw pdns"

if ! su postgres -c "psql -d pdns -tAc \"SELECT to_regclass('public.domains')\"" | grep -q domains; then
  SCHEMA=$(find /usr/share/doc/pdns-backend-pgsql /usr/share/pdns -name 'schema.pgsql*' 2>/dev/null | head -n1 || true)
  if [[ -z "$SCHEMA" ]]; then echo "PowerDNS pgSQL schema not found" >&2; exit 1; fi
  case "$SCHEMA" in
    *.gz) zcat "$SCHEMA" ;;
    *) cat "$SCHEMA" ;;
  esac | su postgres -c "psql -v ON_ERROR_STOP=1 -d pdns"
fi
su postgres -c "psql -d pdns -c 'GRANT ALL ON ALL TABLES IN SCHEMA public TO pdns_rw; GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO pdns_rw; GRANT SELECT ON ALL TABLES IN SCHEMA public TO pdns_ro'"

log "Writing pdns serving config (read-only, 127.0.0.1:5300)"
cat > "$PDNS_CONF" <<EOF
launch=gpgsql
gpgsql-host=127.0.0.1
gpgsql-dbname=pdns
gpgsql-user=pdns_ro
gpgsql-password=$PDNS_DB_RO_PASSWORD
gpgsql-dnssec=yes

local-address=127.0.0.1
local-port=5300
webserver=no
api=no

query-cache-ttl=10
cache-ttl=10
negquery-cache-ttl=10

version-string=anonymous
security-poll-suffix=
disable-axfr=yes
any-to-tcp=yes
edns-subnet-processing=no
EOF
chmod 640 "$PDNS_CONF"
chown root:pdns "$PDNS_CONF" 2>/dev/null || true

log "Writing pdns-api config (writer, webserver 127.0.0.1:8081)"
mkdir -p "$API_CONF_DIR"
cat > "$API_CONF_DIR/pdns.conf" <<EOF
launch=gpgsql
gpgsql-host=127.0.0.1
gpgsql-dbname=pdns
gpgsql-user=pdns_rw
gpgsql-password=$PDNS_DB_RW_PASSWORD
gpgsql-dnssec=yes

api=yes
api-key=$PDNS_API_KEY
webserver=yes
webserver-address=127.0.0.1
webserver-port=8081
webserver-allow-from=127.0.0.1/32
default-api-rectify=yes
default-soa-content=ns1.noghte-dns.example hostmaster.noghte-dns.example 0 10800 3600 604800 300

local-address=127.0.0.1
local-port=5301
control-console=/run/pdns-api
EOF
chmod 640 "$API_CONF_DIR/pdns.conf"
chown root:pdns "$API_CONF_DIR/pdns.conf" 2>/dev/null || true

cat > /etc/systemd/system/pdns-api.service <<'EOF'
[Unit]
Description=PowerDNS Authoritative API/writer (Point DNS Phase 0)
After=network.target postgresql.service pdns.service
Wants=postgresql.service

[Service]
Type=simple
User=pdns
Group=pdns
ExecStart=/usr/sbin/pdns_server --config-dir=/etc/powerdns-api
Restart=on-failure
RestartSec=2
RuntimeDirectory=pdns-api
NoNewPrivileges=yes
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF

log "Writing dnsdist config (public :53 -> 127.0.0.1:5300)"
cat > "$DNSDIST_CONF" <<EOF
setLocal("0.0.0.0:53", { reusePort = true })
newServer({ address = "127.0.0.1:5300", name = "pdns" })
setACL({ "0.0.0.0/0", "::/0" })

setPayloadSizeOnSelfGeneratedAnswers(1232)
addAction(AndRule({QTypeRule(DNSQType.ANY), TCPRule(false)}), TCAction())
addAction(OpcodeRule(DNSOpcode.Update), RCodeAction(DNSRCode.NOTIMP))

setMaxTCPConnectionsPerClient(20)
setMaxTCPQueriesPerConnection(100)

local dbr = dynBlockRulesGroup()
dbr:setQueryRate(300, 10, "Query rate exceeded", 60, DNSAction.Truncate)
dbr:setRCodeRate(DNSRCode.REFUSED, 100, 10, "Too many REFUSED", 60)
dbr:setRCodeRate(DNSRCode.NXDOMAIN, 200, 10, "NXDOMAIN flood", 60, DNSAction.Truncate)
function maintenance() dbr:apply() end

webserver("127.0.0.1:8083")
setWebserverConfig({ password = "$DNSDIST_WEB_PASSWORD", apiKey = "$DNSDIST_API_KEY", acl = "127.0.0.1/32" })
EOF
chmod 640 "$DNSDIST_CONF"

log "Starting and enabling services"
systemctl daemon-reload
systemctl reset-failed pdns pdns-api dnsdist 2>/dev/null || true
systemctl enable postgresql pdns pdns-api dnsdist
# A restart immediately after enable --now can race on /run/pdns/pdns.controlsocket;
# restart exactly once and verify, with one retry.
for svc in pdns pdns-api dnsdist; do
  systemctl restart "$svc" || { sleep 2; systemctl restart "$svc"; }
done
for svc in pdns pdns-api dnsdist; do
  for _ in $(seq 1 20); do systemctl is-active --quiet "$svc" && break; sleep 1; done
  systemctl is-active --quiet "$svc" || { echo "$svc failed to start" >&2; exit 1; }
done

log "Creating health zone via PowerDNS HTTP API"
sleep 2
API="http://127.0.0.1:8081/api/v1/servers/localhost"
if ! curl -fsS -H "X-API-Key: $PDNS_API_KEY" "$API/zones" >/dev/null; then
  echo "PowerDNS API not reachable" >&2; exit 1
fi
if ! curl -fsS -H "X-API-Key: $PDNS_API_KEY" "$API/zones/${ZONE}" >/dev/null 2>&1; then
  curl -fsS -X POST -H "X-API-Key: $PDNS_API_KEY" -H 'Content-Type: application/json' \
    "$API/zones" -d "{\"name\":\"${ZONE}\",\"kind\":\"Native\",\"nameservers\":[\"ns1.noghte-dns.example.\",\"ns2.noghte-dns.example.\"],\"soa_edit_api\":\"DEFAULT\"}" >/dev/null
fi
curl -fsS -X PATCH -H "X-API-Key: $PDNS_API_KEY" -H 'Content-Type: application/json' \
  "$API/zones/${ZONE}" -d "{\"rrsets\":[{\"name\":\"www.${ZONE}\",\"type\":\"A\",\"changetype\":\"REPLACE\",\"ttl\":60,\"records\":[{\"content\":\"${PUBLIC_IP}\",\"disabled\":false}]}]}" >/dev/null

log "Enabling DNSSEC (ECDSA P-256 / algorithm 13)"
if ! curl -fsS -H "X-API-Key: $PDNS_API_KEY" "$API/zones/${ZONE}" | jq -e '.dnssec == true' >/dev/null 2>&1; then
  curl -fsS -X POST -H "X-API-Key: $PDNS_API_KEY" -H 'Content-Type: application/json' \
    "$API/zones/${ZONE}/dnssec/enable" -d '{}' >/dev/null 2>&1 || \
  curl -fsS -X POST -H "X-API-Key: $PDNS_API_KEY" -H 'Content-Type: application/json' \
    "$API/zones/${ZONE}/dnssec/enable" -d '{"algorithm":"ECDSAP256SHA256"}' >/dev/null 2>&1 || \
  curl -fsS -X POST -H "X-API-Key: $PDNS_API_KEY" -H 'Content-Type: application/json' \
    "$API/zones/${ZONE}/cryptokeys" -d '{"keytype":"csk","active":true,"algorithm":"ECDSAP256SHA256"}' >/dev/null
fi
# Rectify so DNSKEY/RRSIG are actually published after key creation.
curl -fsS -X PUT -H "X-API-Key: $PDNS_API_KEY" "$API/zones/${ZONE}/rectify" >/dev/null || true

# The serving instance may have cached REFUSED answers from before the zone
# existed. Purge its caches (restart as a fallback) before asserting answers.
log "Purging serving caches"
pdns_control --socket-dir=/run/pdns purge 2>/dev/null || systemctl restart pdns
sleep 1
ANSWER=$(dig @127.0.0.1 -p 5300 www.${ZONE} A +short | head -n1)
if [[ "$ANSWER" != "$PUBLIC_IP" ]]; then
  echo "Serving instance returned '$ANSWER', expected '$PUBLIC_IP'" >&2
  exit 1
fi

log "Verification"
dig @127.0.0.1 www.${ZONE} A +short
dig @127.0.0.1 ${ZONE} SOA +short
dig @127.0.0.1 ${ZONE} DNSKEY +dnssec +short | head -5
curl -fsS -H "X-API-Key: $PDNS_API_KEY" "$API/zones/${ZONE}/cryptokeys" | jq -r '.[].ds[]?' || true
systemctl --no-pager --plain status pdns pdns-api dnsdist | grep -E 'Active:|Loaded:' || true
log "Done. Secrets: $SECRETS_FILE (chmod 600); API key is there, never in Git."
