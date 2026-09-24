# PLAN — Client-Only SASE Adoption (No Server Changes)

**نقطه (Noghte) alignment · client-side-only track**

Goal: push the Android client as far toward the نقطه SASE requirements as possible **without touching any backend/edge server**. Everything in this plan works against the *current* Django backend (`api.clouda.ir`) and existing Trojan upstreams.

Scope rule: if a change requires new server code, new server config, or a new server service → it is **out of scope** here (see [`PLAN-SASE-FULL.md`](PLAN-SASE-FULL.md)).

---

## 1. What SASE can/cannot be done client-side

| نقطه requirement | Client-only feasible? | Notes |
|---|---|---|
| Tunneling / SD-WAN (edge selection) | ⚠️ Partial | Multi-server config + client-side server selection/failover; no server coordination |
| ZTNA (per-app, per-identity policy) | ⚠️ Partial | On-device enforcement only (per-app split tunnel, on-device rules); no IdP/OPA |
| Device Trust | ✅ Yes | Play Integrity verdict stored locally, gate "Connect" on it (self-attestation) |
| SWG (web filtering) | ✅ Mostly | On-device domain/category blocklists enforced via Xray routing + DNS |
| FWaaS | ⚠️ Partial | Local L3/L4 policy via Xray routing rules (block ports/IPs/QUIC); true L7 DPI needs edge |
| DLP | ❌ No (real) | Best-effort: block known exfil destinations; content inspection needs edge |
| CASB | ❌ No | Requires edge/API integration |
| PQC (ML-KEM/ML-DSA) | ❌ No (handshake) | Hybrid TLS needs server support. **Can** build crypto-agility + readiness now (§6) |
| MFA/SSO | ❌ No | Needs IdP (Keycloak) |
| Cert pinning, Keystore, log hygiene | ✅ Yes | Pure client hardening |

**Ceiling:** ~45–50% of the نقطه v1.0 client-side requirement surface (today ≈ 20%).

---

## 2. Phase 0 — Security & Release Hygiene (Week 1–2)

Baseline fixes; prerequisites for everything else.

- [ ] **Remove `clouda-release.keystore` from git history**; rotate signing key; move secrets to CI secrets (`app/build.gradle.kts:29-36`)
- [ ] Enable R8/minify for release (`isMinifyEnabled = true`); verify `proguard-rules.pro` keep rules for Xray/OkHttp/Compose
- [ ] Delete dead code: `dns/` package (355 lines), `ui/components/StatusCard.kt`, `ui/components/DomainList.kt`, unstaged API methods never called
- [ ] Fix stale version label in `SettingsScreen.kt:113` → read from `BuildConfig.VERSION_NAME`
- [ ] Add baseline unit tests (TrojanUrlParser, FakeIpMap, DomainRouter) + instrumented smoke (VPN start/stop) — target: CI gate
- [ ] CI: add `lint` + `testDebugUnitTest` job before APK build (`.github/workflows/build-apk.yml`)

**Exit criteria:** clean tree, green CI with tests, signed release from CI-injected secrets.

## 3. Phase 1 — Identity, Keys, TLS Trust (Week 2–4)

Client-side ZTNA building blocks (local only):

- [ ] **Keystore-backed secrets**: migrate Trojan password / tokens from plain `CloudaPrefs` to `EncryptedSharedPreferences` (AES-256-GCM key in Android Keystore, `setIsStrongBoxBacked` when available)
- [ ] **Certificate pinning** for all `network/api/` calls: OkHttp `CertificatePinner` on `api.clouda.ir`/`my.clouda.ir` SPKI hashes (+ backup pin); fail-closed
- [ ] **Play Integrity attestation**: request verdict before allowing Connect; store verdict + timestamp locally; UX copy explains "Device Trust". (Server-side verification not required for self-attestation mode)
- [ ] Replace spoofable `ANDROID_ID` identity (`CloudaPrefs.kt:13-20`) with random UUID v4, generated once, Keystore-encrypted, non-exportable
- [ ] **Log hygiene**: scrub password/token/SNI from all `Log.*` and Xray stderr mirroring; release builds disable verbose Xray loglevel
- [ ] Screen-lock gate option in Settings: require device unlock (BiometricPrompt/device credential) before Connect — local "MFA"

## 4. Phase 2 — On-Device SWG-lite + DNS Security (Week 4–7)

Delivered entirely through `XrayConfigGenerator` routing/DNS rules + local lists:

- [ ] **Category blocklists** (ads/trackers/malware/phishing/18+): bundled seed lists + remote fetch (same pattern as `DomainFetcher`); UI section "Web Protection" with category toggles
- [ ] Rules → `blackhole` outbound: `domain:` entries, `geosite:category-ads-all`, `geosite:category-porn` (ship `geosite.dat` asset)
- [ ] **DNS-over-HTTPS upstream**: Xray `dns` → `https://dns.google/dns-query` / Cloudflare for non-bypass domains instead of plain `8.8.8.8` UDP; FakeDNS stays for bypass list
- [ ] Per-user **custom blocklist** (Domains screen: "blocked" tab) — same storage path as bypass list
- [ ] **QUIC policy toggle** (currently hard-blocked UDP/443): allow | block | bypass-only
- [ ] **Phishing guard**: block freshly-registered/lookalike patterns via optional list (e.g., openphish feed), cached 6h

**Exit criteria:** with protection toggles on, test domains (ads/malware test pages) fail; latency overhead < 5%.

## 5. Phase 3 — Traffic Governance (FWaaS-lite) + Kill Switch (Week 7–10)

- [ ] **Per-app split tunneling UI**: installed-app list (icon/label), include/exclude mode → `VpnService.addAllowedApplication` / `addDisallowedApplication` (self-exclusion exists at `CloudaVpnService.kt:133`)
- [ ] **Local firewall** section in Settings:
  - [ ] Block all traffic when VPN drops (**kill switch**: `setBlocking(true)` + `Builder.setMetered`/reconnect logic + Always-on VPN intent handoff `Settings.ACTION_VPN_SETTINGS`)
  - [ ] Block private/LAN ranges toggle (RFC1918 via Xray routing)
  - [ ] Per-port rules (e.g., block outbound 25/445) via Xray `port` rules
- [ ] **Bypass vs global mode**: current domain-list mode OR full-tunnel mode toggle (routing default → proxy)
- [ ] Health: latency test (HTTPS handshake time to upstream) + auto server-order hint; surface in StatusCard

## 6. Phase 4 — PQC Readiness (Crypto-Agility) (Week 10–14)

Server can't do hybrid handshake yet, so client builds the *capability* and *abstraction*:

- [ ] **Crypto-agility layer**: config schema `crypto: { kex: "x25519" | "x25519_mlkem768", sig: "ecdsa" | "mldsa65", mode: "classic"|"hybrid" }` in `AppConfig`/`XrayConfigGenerator`, capability negotiation field in client hello (metadata), runtime fallback
- [ ] Integrate **liboqs JNI** module (or BoringSSL-with-OQS build) as optional native lib; benchmark ML-KEM-768 keygen/encaps on mid-range devices (target: handshake overhead < 15%)
- [ ] Xray version bump to latest + evaluate `reality`/`utls` updates so hybrid TLS 1.3 (X25519+ML-KEM-768, group `X25519MLKEM768` id 0x11EC) activates the moment *any* upstream supports it — zero client rewrite
- [ ] Interop lab mode (debug build): point client at a local OQS-enabled TLS server (dev workstation) to prove hybrid handshake path end-to-end
- [ ] Document evidence for نقطه compliance: handshake capture, benchmark table → feeds `SASE-Compliance-Report`

## 7. Phase 5 — Reliability & Observability (Week 14–16)

- [ ] **WorkManager** periodic domain/blocklist refresh (replaces connected-only coroutine loop, `ProxyManager.kt:108-120`)
- [ ] Crash recovery + sentinel file + local crash-log persistence (extends `CloudaApp.kt:14-18` handler)
- [ ] On-device stats: session time, upload/download per session, per-app usage (NetworkStatsManager) — dashboard card
- [ ] arm32 (`armeabi-v7a`) binary build + CI matrix (or explicit drop decision documented)
- [ ] 30-day stability runbook: watchdog coverage review (`XrayManager.kt:149-166`), process-death matrix tests

---

## Effort & outcome

| Phase | Est. effort | نقطه surface gained |
|---|---|---|
| 0 Hygiene | 1–2 wk | — (baseline trust) |
| 1 Identity/Keys/TLS | 2 wk | Device Trust, Keystore, pinning |
| 2 SWG-lite + DNS | 3 wk | SWG (on-device) |
| 3 FWaaS-lite + kill switch | 3 wk | Partial FWaaS, SD-WAN-lite |
| 4 PQC readiness | 3–4 wk | Crypto-agility, hybrid-ready |
| 5 Reliability | 2 wk | Ops maturity |
| **Total** | **~14–16 wk, 1 dev** | **≈ 20% → ~45–50%** |

**Explicit non-goals (need server):** ZTNA policy plane (Keycloak/OPA), true L7 FWaaS, TLS-inspection SWG, CASB, DLP content inspection, hybrid-PQC handshake in production, SSO/MFA, centralized telemetry. → all in `PLAN-SASE-FULL.md`.
