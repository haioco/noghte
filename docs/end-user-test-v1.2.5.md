# HaioBypass v1.2.5 — End-User Test (MCP-driven)

- **APK**: `app-release.apk` — sha256 `1d2653d55b46ff18fe1188dcd58cd53f99968d5d4f6c6bd5b15d6c8aee83f32f` (the published release asset)
- **Version**: 1.2.5 (versionCode 8) — signed with `haio-release` key
- **Environment**: Android 14 (API 34) / Pixel 5 profile — x86_64 emulator on Haio PaaS (`android-avd-simulator`, app 311), driven via `mcp.haio.ir` `android_testing.*` tools
- **Date**: 2026-09-23
- **Method**: fresh install via `run_test` (auto-launch passed) → interactive UI driving: `dump_ui` (element map), `tap`, `input_text`, `press_key`, `screenshot`, `shell ps`

## Preconditions

- Fresh session, no saved config (placebo: first launch after install)
- Runtime permissions pre-granted by the harness (POST_NOTIFICATIONS etc.)

## Steps & Results

| # | User action | Expected | Actual | Screenshot |
|---|---|---|---|---|
| 1 | Launch app | Home screen renders: header `v1.2.5 HaioBypass`, big toggle, status card, config row, domains row, tab bar (خانه/فروشگاه/دامنه‌ها/تنظیمات) | ✅ All elements present; texts: «برای اتصال ضربه بزنید», «وضعیت اتصال: قطع شده», «هیچ دامنه‌ای بارگذاری نشده ۰» | `screenshots/01-home.png` |
| 2 | Tap فروشگاه tab | Store screen with plans | ✅ «Basic 5GB — ۱۵۰۰۰ تومان», «Pro 20GB — ۵۰۰۰۰ تومان», «خرید با کیف پول» buttons render | `screenshots/02-store.png` |
| 3 | Tap دامنه‌ها tab | Domains screen | ✅ «آخرین دریافت: هرگز», search field «جستجوی دامنه...», «۰ دامنه بارگذاری شد» | `screenshots/03-domains.png` |
| 4 | Tap تنظیمات tab | Settings screen | ✅ عمومی: «اجرای خودکار در بوت» toggle; شبکه: «پورت SOCKS ۱۰۸۰۸», «سرور DNS ۸.۸.۸.۸», «DNS جعلی ۱۰.۰.۰.۱»; درباره section | `screenshots/04-settings.png` |
| 5 | Return to خانه | Home state preserved (no reload/reset) | ✅ State intact; nav round-trip lossless | — |
| 6 | Tap config row «تنظیمات تروجان» → enter `trojan://testpass@portal.haio.ir:443?sni=portal.haio.ir` → ذخیره | URL parsed, saved, Home shows server/SNI/port | ✅ Saved; Home card shows «سرور portal.haio.ir», «SNI portal.haio.ir», «۴۴۳» — persistence (`apply()`) verified | `screenshots/06-config-entry.png` |
| 7 | Tap the big toggle | System VPN consent dialog («HaioBypass wants to set up a VPN connection…») | ✅ Dialog appears; OK/Cancel buttons found via dump | `screenshots/07-connecting.png` |
| 8 | Tap OK | VpnService starts; connecting state; on failure return to «قطع شده» **without crash** | ✅ Service start + graceful failure; app returns to disconnected state | `screenshots/08-final-state.png` |
| 9 | Verify process alive after full flow | `com.haio.bypass` process running | ✅ `ps`: `u0_a192 … S com.haio.bypass` — no crash at any point | — |

## Emulator limitations (not app bugs)

- **Tunnel establishment cannot complete**: the shipped xray/tun_wrapper/tun2socks binaries are arm64-only; the x86_64 emulator cannot exec them, so «متصل» / `tun2socks started successfully` is not reachable. The graceful-failure path IS exercised (binary exec failure → app recovers, no crash) — same code path as a corrupted-binary failure on a real device.
- **Transient «در حال اتصال» state**: too short to capture with per-request dumps on x86 (fails in <1s). Needs a real arm64 device to observe the pulse animation + connecting UI.

## Verdict

**PASS** — install, first-run, navigation (all 4 tabs), config entry + persistence, VPN consent, service start, graceful failure: all user flows complete with zero crashes on Android 14. Matrix runs also passed on Android 12/13/15/16 (`compatibility_run`, 2026-09-23).

## Replay

Reproduce with the MCP tools (session from `android_testing.run_test`):

```
dump_ui → parse bounds → tap tab centers: فروشگاه (679,2164) دامنه‌ها (403,2164) تنظیمات (127,2164) خانه (954,2164)
tap config row (540,1518) → tap field (540,719) → input_text trojan://… → press_key 4 (keyboard) → tap ذخیره (278,964)
tap toggle (540,576) → dump_ui → tap VPN OK (888,1507) → dump_ui (status) → shell ps (alive)
```

> Coordinates are for the 1080×2340 Pixel-5 profile; re-derive from `dump_ui` bounds for other profiles. Note RTL: primary buttons (ذخیره) are on the **left** half.
