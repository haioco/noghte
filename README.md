# Noghte / Point (نقطه)

این ریپو هر دو محصول «نقطه» را در خود جای می‌دهد:

| محصول | چه | کجا |
|---|---|---|
| نقطه — DNS معتبر (Point DNS) | میزبانی DNS معتبر با DNSSEC، پنل فارسی و REST API (فاز ۰) | `docs/point-dns/` (مدارک)، `deploy/point-dns/` (استقرار)، پنل به‌صورت افزونهٔ Odoo در ریپوی کلودا |
| نقطه — اپ SASE اندروید (HaioBypass) | کلاینت دسترسی امن آنتی‌تحریم (Kotlin + Compose) | `app/`، `backend/` |

## مستندات

* `docs/point-handbook_v4.html` — **سند اصلی محصول**: مرجع یکپارچهٔ خانوادهٔ
  Point (نقشهٔ راه فاز ۰ تا ۵؛ فاز ۰ = Point DNS)
* `docs/point-dns/` — مستند افزونهٔ Odoo، یکپارچه‌سازی با کلودا، شواهد تأیید،
  طرح اولیهٔ نسخهٔ ۱ (`point-v1.1-plan.html`)
* `docs/reference/` — راهنماهای مرجع Point و سند مرجع DeepSeek
* `docs/sase/` — مدارک سرمایه‌گذاری/پیشنهاد SASE + اسکریپت‌های ساخت DOCX
  (کپی؛ اصل برخی فایل‌ها در `Funding/NoghteSASE`)
* `docs/end-user-test-v1.2.5.md` — تست کاربر نهایی اپ اندروید
* سایر اسناد در ریشه: `PLAN-SASE-FULL.md`، `PLAN-SASE-CLIENT-ONLY.md`،
  `Haio_API_Documentation-antisanction.html`، `noghte-insight-onepage.html`،
  `noghte-proposal-filled.docx`
* ایمیج نماد: `docs/noghte-emblem.png`

## اپ اندروید (HaioBypass)

* Application ID: `com.noghte.app`
* Min SDK 26، target/compile SDK 34

```bash
./build.sh debug
./build.sh release
```

ساخت با مرجع `BUILD.md`.

## DNS

سرور زندهٔ فاز ۰: `noghte-dns-01` (۹۴.۱۸۲.۱۷۲.۹۶) — PowerDNS + dnsdist؛ نصب و
سخت‌سازی در `deploy/point-dns/`. یافته‌ها و تصحیح‌ها در
`deploy/point-dns/README.md`.

## قواعد کار

هر تغییر با تسک روی برد موضوع و مسائل گیت‌هاب همراه است (`dev-tasks`). کد پنل
DNS در ریپوی کلودا است و قواعد همان ریپو (شاخه + MR) را می‌گیرد.