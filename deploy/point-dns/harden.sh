#!/usr/bin/env bash
# Phase 0 hardening pass for an already-installed Point DNS single node.
#
# Fixes verified on noghte-dns-01 (94.182.172.96, 2026-11-26):
#   1. Out-of-zone recursion — google.com/youtube.com/facebook.com/instagram.com
#      answered NOERROR with `ra ad` (a validating upstream was in the dnsdist
#      pool), while example.net correctly returned REFUSED. Rewriting the
#      canonical config removes every upstream except the local serving engine.
#   2. `id.server CHAOS TXT` answered with the VM hostname. CHAOS class is now
#      REFUSED.
#   3. ANY queries were not truncated/refused on dnsdist 1.8.3 (ANY rule with
#      the DNSQtype.ANY constant does not match). ANY is now REFUSED on UDP and
#      TCP via the numeric qtype.
#
# Run as root on the VM:   bash harden.sh [config-file]
set -euo pipefail

CONF_SRC="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/dnsdist.conf}"
DNSDIST_CONF=/etc/dnsdist/dnsdist.conf
SECRETS_FILE=/etc/noghte-dns/secrets.env
PROBE_ZONE="probe.noghte-dns.example."

log() { echo "[harden-point-dns] $*"; }

if [[ $EUID -ne 0 ]]; then echo "Run as root" >&2; exit 1; fi
[[ -f "$CONF_SRC" ]] || { echo "missing $CONF_SRC" >&2; exit 1; }
[[ -f "$SECRETS_FILE" ]] || { echo "missing $SECRETS_FILE" >&2; exit 1; }
# shellcheck disable=SC1090
source "$SECRETS_FILE"

log "Current dnsdist upstream/pool lines (evidence, before the change):"
grep -nE 'newServer|setLocal|addAction|forward' "$DNSDIST_CONF" || echo "  (none found)"

STAMP=$(date +%Y%m%d_%H%M%S)
cp -a "$DNSDIST_CONF" "${DNSDIST_CONF}.bak.${STAMP}"
log "Backup: ${DNSDIST_CONF}.bak.${STAMP}"

log "Installing canonical dnsdist config from $CONF_SRC"
sed -e "s|@DNSDIST_WEB_PASSWORD@|${DNSDIST_WEB_PASSWORD}|g" \
    -e "s|@DNSDIST_API_KEY@|${DNSDIST_API_KEY}|g" \
    "$CONF_SRC" > "$DNSDIST_CONF"
chmod 640 "$DNSDIST_CONF"

log "Validating config"
if dnsdist --help 2>&1 | grep -q -- "--check-config"; then
  if dnsdist --check-config --config "$DNSDIST_CONF"; then
    log "dnsdist --check-config: OK"
  else
    log "dnsdist config check FAILED; restoring backup" >&2
    cp -a "${DNSDIST_CONF}.bak.${STAMP}" "$DNSDIST_CONF"
    exit 1
  fi
else
  log "dnsdist has no --check-config on this version; restart is the check"
fi

log "Restarting dnsdist"
systemctl restart dnsdist
for _ in $(seq 1 20); do systemctl is-active --quiet dnsdist && break; sleep 1; done
systemctl is-active --quiet dnsdist || { echo "dnsdist failed to start" >&2; exit 1; }

log "Asserting serving engine is authoritative-only (pdns.conf drift check)"
PDNS_CONF=/etc/powerdns/pdns.conf
for setting in "webserver=no" "api=no" "version-string=anonymous" "disable-axfr=yes"; do
  grep -qx "$setting" "$PDNS_CONF" || echo "  WARNING: '$setting' missing from $PDNS_CONF"
done

log "Verification (all queries against 127.0.0.1:53)"
V1=$(dig +short @127.0.0.1 www.${PROBE_ZONE} A | head -n1)
V2=$(dig @127.0.0.1 google.com A +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)
V3=$(dig @127.0.0.1 youtube.com A +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)
V4=$(dig @127.0.0.1 www.${PROBE_ZONE} ANY +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)
V5=$(dig @127.0.0.1 id.server CHAOS TXT +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)
V6=$(dig @127.0.0.1 ${PROBE_ZONE} SOA +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)
V7=$(dig @127.0.0.1 www.${PROBE_ZONE} A +dnssec +noall +comments | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1)

fail=0
report() { if [[ "$2" == "$3" ]]; then echo "  OK   $1 -> $2"; else echo "  FAIL $1 -> $2 (expected $3)" >&2; fail=1; fi; }
report "probe www A answer" "${V1:-<empty>}" "94.182.172.96"
report "google.com (out-of-zone)" "$V2" "REFUSED"
report "youtube.com (out-of-zone)" "$V3" "REFUSED"
report "ANY (probe zone)" "$V4" "REFUSED"
report "id.server CHAOS TXT" "$V5" "REFUSED"
report "probe SOA" "$V6" "NOERROR"
report "probe www +dnssec" "$V7" "NOERROR"

# UPDATE must be NOTIMP (opcode 5).
# NOTE: nsupdate exits 2 when the server refuses the update ("update failed:
# NOTIMP") — i.e. on success of this check. With `set -euo pipefail` that would
# abort the script before the report, so every pipeline below ends in `|| true`
# and the assertion is made on the *parsed text*, not on the exit status.
UPD=$(dig @127.0.0.1 +opcode=update +noall +comments 2>/dev/null | sed -n 's/.*status: \([A-Z]*\).*/\1/p' | head -1 || true)
if command -v nsupdate >/dev/null 2>&1; then
  UPD=$(printf 'server 127.0.0.1\nzone %s\nupdate add x.%s 60 A 127.0.0.1\nsend\n' "$PROBE_ZONE" "$PROBE_ZONE" | timeout 10 nsupdate 2>&1 | grep -o 'NOTIMP' | head -1 || true)
  report "UPDATE (nsupdate)" "${UPD:-<none>}" "NOTIMP"
else
  report "UPDATE (dig +opcode)" "${UPD:-<unknown>}" "NOTIMP"
fi

if [[ $fail -ne 0 ]]; then
  echo "Hardening verification FAILED — rollback: cp ${DNSDIST_CONF}.bak.${STAMP} ${DNSDIST_CONF} && systemctl restart dnsdist" >&2
  exit 1
fi
log "Done — authoritative-only, CHAOS refused, ANY refused, UPDATE NOTIMP."