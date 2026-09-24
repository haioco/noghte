# PLAN — Full SASE Adoption (Client + Server + Edge)

**نقطه (Noghte) v1.0 target · 6 months · 4 phases**

Full adoption of the نقطه requirements per `NoghteSASE/` docs: three-layer architecture (Cloud Control Plane / Security Edge / Endpoint) with Hybrid Post-Quantum Cryptography, aligned to the ۶-month / ۴-phase roadmap in the proposal. Client phases inherit from [`PLAN-SASE-CLIENT-ONLY.md`](PLAN-SASE-CLIENT-ONLY.md) — this plan adds everything that was "out of scope (needs server)" there.

Today state (assessed from codebase): client VPN core complete (v1.2.4, Trojan-over-TLS via Xray, fake-IP domain routing); backend = Django billing/provisioning only. **Overall نقطه readiness ≈ 20%.** Target: **100% of نقطه v1.0.**

---

## Architecture (target)

```
┌─────────────────────── CLOUD CONTROL PLANE ───────────────────────┐
│ Keycloak (OIDC/SAML, MFA) · OPA (policy-as-code) · Vault (PKI,    │
│ ML-DSA certs) · Mgmt Dashboard + Grafana · Django (billing,       │
│ provisioning, device inventory, orgs) — PostgreSQL                │
└──────────────┬────────────────────────────────────┬──────────────┘
        policy │ push (REST/gRPC)                    │ telemetry
┌──────────────▼────────────────────────────────────▼──────────────┐
│ SECURITY EDGE (SSE) — own edge nodes (multi-region)              │
│ ZTNA Gateway · FWaaS (eBPF/nftables L7) · SWG (Squid+ICAP,       │
│ optional TLS inspection) · DNS Protect · CASB (SaaS app ctrl) ·   │
│ DLP (patterns) · Tunnel: TLS 1.3 HYBRID X25519+ML-KEM-768        │
│ (OQS-enabled Xray fork / WireGuard+PQC), cert: ML-DSA-65         │
└──────────────┬───────────────────────────────────────────────────┘
               │ hybrid PQC tunnel (AES-256-GCM bulk)
┌──────────────▼───────────────────────────────────────────────────┐
│ ENDPOINTS — Android client (evolved CloudaBypass), desktop later   │
│ Keystore secrets · Play Integrity · per-app policy · SWG-lite    │
│ cache · anti-sanction core (800+ sanctioned domains, Fake-IP)    │
└──────────────────────────────────────────────────────────────────┘
```

Anti-sanction core (unique differentiator) preserved at every layer: domain-based sanctioned-service detection, Fake-IP DNS routing, upstream failover, offline list cache.

---

## Phase 1 — Hybrid PQC Tunnel (Month 1)

*Deliverable: production hybrid-PQC tunnel, client v2.0.*

**Server/edge**
- [ ] Fork/patch Xray-core (or sidecar OQS-terminator) with **OQS-OpenSSL / oqs-provider**: TLS 1.3 group `X25519MLKEM768`, cert chain signed **ML-DSA-65**, root long-term with **SLH-DSA**; AES-256-GCM bulk unchanged
- [ ] Key/cert issuance pipeline via Vault PKI (ML-DSA); rotation automation; dual classic+PQC listeners during migration (crypto-agility negotiation)
- [ ] Performance lab: handshake latency + bulk throughput vs classic; acceptance: **overhead < 15%** on mid-range Android

**Client** (continues client-only Phase 4, now for real)
- [ ] Enable production `hybrid` mode in `XrayConfigGenerator`; negotiation + safe fallback to classic for legacy servers
- [ ] liboqs JNI or BoringSSL-OQS shipped in AAB; ML-DSA server-cert verification; pin root
- [ ] A/B rollout flags via backend config endpoint

**Backend (Django)**
- [ ] Extend subscription provisioning to issue **per-user, per-device** Xray credentials (replace shared password URLs); revoke API
- [ ] Device inventory model (device pubkey, Play Integrity verdict store, last-seen)

**Exit criteria:** hybrid handshake in production for pilot users; classic fallback proven; KAT vectors for ML-KEM/ML-DSA in CI.

## Phase 2 — Zero Trust + SSE Edge Core (Months 2–3)

*Deliverable: ZTNA policy plane + FWaaS/SWG on edge nodes.*

**Control plane**
- [ ] **Keycloak** realm: orgs, users, groups; OIDC login in Android (AppAuth), MFA enrollment; SSO for admin console
- [ ] **OPA** sidecar: policies-as-code repo (who × device-trust × app × time → allow/deny); Django pushes policy bundles; edge pulls signed bundles
- [ ] Device Trust enforcement: Play Integrity verdict validated **server-side** at connect; step-up MFA policy hooks

**Edge**
- [ ] **ZTNA gateway** mode: per-app access decisions (not just full tunnel); connectivity via existing tunnel + policy tags
- [ ] **FWaaS**: nftables + eBPF classifier on edge; L7 rules per policy (app-port-geo); rate limiting; QUIC policy
- [ ] **SWG**: Squid + ICAP for category filtering at edge (central blocklists from client Phase 2 become server-authoritative); optional TLS inspection with per-org enterprise cert (BYO-cert; off by default)
- [ ] Per-user egress accounting (replaces client-side metering)

**Client**
- [ ] OIDC login flow; token lifecycle; policy sync; per-app mode becomes ZTNA "app access" UX
- [ ] "Block page" UX for edge-denied destinations

**Exit criteria:** two pilot orgs on ZTNA policies; policy change propagates edge < 60s; category block enforced at edge with client VPN on.

## Phase 3 — Control Plane, CASB/DLP, Crypto-Agility (Month 4)

*Deliverable: org admin experience + data protection.*

**Control plane**
- [ ] Admin dashboard (orgs, users, devices, policies, edge health) — React/Next in Django admin or separate; **Grafana** stack (Prometheus on edges, Loki logs)
- [ ] Audit log (immutable, per-org retention)
- [ ] **SLH-DSA** root/ICA for long-term signatures; full crypto-agility matrix (algorithm swap w/o client release)

**Edge**
- [ ] **CASB-lite**: SaaS app catalog ( sanctioned + unsanctioned ), per-org allow/deny, shadow-IT discovery report from (consented) edge logs
- [ ] **DLP-lite**: pattern rules (card numbers, national ID, keywords) on inspected flows where TLS inspection enabled; block/alert actions
- [ ] SD-WAN: multi-edge anycast-ish steering, per-org preferred egress, failover (client measures + edge health API)

**Client**
- [ ] Anti-sanction list → server-managed signed bundles (signed with ML-DSA) with client signature verification; offline cache retention
- [ ] Org enrollment flow (QR/invite link), per-org config isolation, multi-profile

**Exit criteria:** admin can onboard an org, push policy, see usage + shadow-IT report end-to-end; DLP test vectors block; signed domain-bundle verification passes negative tests.

## Phase 4 — Hardening, Compliance, Launch (Months 5–6)

*Deliverable: نقطه v1.0 GA + compliance evidence pack.*

- [ ] External **penetration test** (client, edge, control plane); fix & retest
- [ ] **FIPS 140-3 alignment**: module inventory, boundary doc, algorithm certs (operate via OQS-based validated path where applicable); self-assessment workbook
- [ ] Load test: per-edge 10k concurrent tunnels target; chaos drills (edge loss, control-plane loss)
- [ ] Success runbooks, on-call, status page; SLA machinery (99.9% dashboard)
- [ ] Compliance self-audit vs `NoghteSASE/SASE-Compliance-Report.html`; produce signed gap report = 0 critical gaps
- [ ] **GA launch**: نقطه v1.0, 5 pilot orgs live, pricing activation (proposal tiers: رایگان / حرفه‌ای / سازمانی)
- [ ] Docs: admin guide, security whitepaper, PQC migration guide, API docs

---

## Cross-cutting workstreams (all phases)

| Workstream | Owner | Notes |
|---|---|---|
| Anti-sanction core evolution | Backend+Client | Sanctioned-domain pipeline, ML-DSA signed bundles, upstream failover across edges |
| CI/CD hardening | DevOps | Keystore out of repo (client Phase 0), signed artifacts, staged rollout, edge image builds |
| Privacy/legal | Ops | Data-minimization policy, inspection-consent UX, org data residency options |
| Desktop clients | Client (stretch) | Windows/Linux reuse of edge + control plane (Tauri/Rust reuse from desktop CloudaBypass) |

## Team & budget (matches proposal)

- 5 FTE × 6 months (Android, backend/Django, edge/network, security/crypto, DevOps)
- Budget: **13,700M ریال** total — split 50% معاونت / 30% مجری / 20% سایر (see `noghte-proposal-filled.docx`)

## KPIs

| Metric | Phase gate |
|---|---|
| Hybrid-PQC handshake overhead | < 15% (P1) |
| Policy→edge propagation | < 60s (P2) |
| Edge capacity | 10k tunnels/edge (P4) |
| Uptime (edges) | ≥ 99.9% Q after GA |
| Critical vulns open at launch | 0 (P4) |
| Pilot orgs live | 5 (P4) |

## Key risks & mitigations

| Risk | Mitigation |
|---|---|
| OQS/Xray integration fragility | Sidecar terminator fallback; dual listeners during migration |
| TLS-inspection trust/legal pushback | Off by default; per-org BYO-cert; documented consent UX |
| Single-team bus factor | Docs-as-code from P1; pairing on crypto modules |
| Edge infra cost creep | Start 2 edges; autoscale plan only after P3 metrics |
