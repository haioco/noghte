# نقطه | Noghte (Point DNS) — Odoo addon V0.1

پنل مفهومی مدیریت DNS معتبر (Authoritative DNS) برای پلتفرم کلودا، بر پایه
`point-v1.1-plan.html`. این نسخه **فقط مفهوم و رابط کاربری** است: مدل داده و
جریان‌های UX کامل هستند، اما موتور DNS (PowerDNS)، کارگر تأیید NS و آمار واقعی
هنوز وصل نشده‌اند.

## دامنه نسخه ۰٫۱

| در دامنه | بیرون از دامنه |
|---|---|
| ساخت و فهرست ناحیه، جست‌وجو و فیلتر وضعیت | اتصال به PowerDNS / dnsdist |
| ویرایش رکورد با پیش‌نویس و اعمال اتمیک | Anycast و BGP |
| واردسازی / خروجی BIND | AXFR/IXFR، DoH/DoT |
| DNSSEC (نمایشی) و رکورد DS | چرخش خودکار کلید و KSK rollover |
| واگذاری NS (شبیه‌سازی تأیید) | کارگر واقعی بررسی والد |
| آمار ساعتی (داده نمایشی) | جمع‌آوری واقعی از dnstap |
| قالب GitHub Pages با پیش‌نمایش تفاوت | قالب‌های Vercel/Netlify |
| توکن API، تیم و امنیت (پایه) | صورتحساب و پرداخت |

## نصب

```bash
# داخل کانتینر Odoo با addons-path شامل Bodoo/extra-addons
odoo -d <db> -i point_dns --stop-after-init
```

وابستگی‌ها: `base`, `web`, `portal`, `website`, `cloud_core`, `burna_layout`,
`clouda_web_assets`, `haio_domain_cso`.

پس از نصب:

* پنل مشتری: `/point` (سایدبار «نقطه» در پنل یکپارچه کلودا)
* پیشخوان کارکنان: `/point/staff` (فقط `base.group_system`)
* منوی بک‌اند: **نقطه** (ناحیه‌ها، طرح‌ها، تاریخچه، توکن‌ها، اعضا، آمار)
* API: `/api/point/v1/...` با `Authorization: Bearer pt_live_...`

## صفحه‌ها

| مسیر | توضیح |
|---|---|
| `/point` | پیشخوان: KPI، نیازمند اقدام، رویدادهای اخیر، ناحیه‌های اخیر |
| `/point/zones` | فهرست ناحیه‌ها با جست‌وجو، فیلتر و شمارش وضعیت |
| `/point/zones/new` | ساخت ناحیه (نام، طرح، رکوردهای پایه) |
| `/point/zones/<id>` | تب‌های رکوردها، NS، DNSSEC، آمار، تاریخچه، تنظیمات |
| `/point/zones/<id>/import` | پیش‌نمایش و ثبت BIND |
| `/point/zones/<id>/templates` | گالری قالب‌ها و اعمال‌شده‌ها |
| `/point/settings/team` | اعضای تیم و نقش‌ها |
| `/point/settings/tokens` | ساخت/ابطال توکن API |
| `/point/settings/security` | TOTP و نشست‌ها (نمایشی) |
| `/point/staff` | جست‌وجو، تعلیق/رفع تعلیق با ثبت دلیل |

## معماری داخلی

```
models/
  point_plan.py        طرح و محدودیت‌ها
  point_zone.py        ناحیه، چرخه عمر، DS، apply_changes
  point_rrset.py       مجموعه رکورد (name + type + ttl)
  point_record.py      مقدارهای یک مجموعه
  point_audit.py       تاریخچه فقط‌افزودنی
  point_token.py       توکن API (فقط هش SHA-256)
  point_member.py      اعضای تیم
  point_template.py    قالب‌های اعمال‌شده
  point_usage.py       آمار ساعتی
services/
  validation.py        قواعد نام/TTL/نوع و اعتبارسنجی دسته‌ای
  bind.py              تجزیه، خروجی و diff فایل BIND
  templates.py         قالب GitHub Pages: پارامتر، پیش‌نمایش، اعمال
  stats.py             سری زمانی و ترکیب QTYPE (نمایشی)
  presentation.py      ارقام فارسی و تاریخ جلالی
controllers/
  portal.py            صفحه‌های پنل (QWeb)
  api.py               REST /api/point/v1
```

* رکوردها از نوع `cloud.dns.record.type` استفاده می‌کنند؛ انواع `SRV`، `CAA` و
  `PTR` در همین افزونه به داده‌های `haio_domain_cso` اضافه می‌شوند.
* رابط کاربری داخل پوسته پنل موجود (`burna_layout.burna_panel_base`) و با
  آیتم‌های `burna.menu.item` در سایدبار قرار می‌گیرد.
* فونت‌ها از `clouda_web_assets` و استایل‌ها از `static/src/css/point.css`
  (توکن‌های طراحی سند، RTL منطقی، حالت تاریک) می‌آید.
* تاریخ‌ها جلالی، ارقام متن فارسی و مقادیر فنی لاتین/مونو هستند.

## الگوی API (نمونه)

```bash
curl -H "Authorization: Bearer pt_live_..." \
     https://<host>/api/point/v1/zones

curl -X PUT -H "Authorization: Bearer pt_live_..." \
     -H "Content-Type: application/json" \
     -d '{"ttl":300,"records":["192.0.2.10"]}' \
     https://<host>/api/point/v1/zones/1/rrsets/@/A
```

خطاها با `application/problem+json` و فیلدهای `type/title/status/detail/request_id`
برمی‌گردند.

## آزمون

```bash
odoo -d <db> -i point_dns --test-tags /point_dns --stop-after-init
```

آزمون‌ها: نرمال‌سازی نام و Punycode، TTL و قواعد A/MX/CNAME، یکتایی ناحیه،
اعمال دسته‌ای و افزایش سریال، ممنوعیت CNAME در ریشه، رفت‌وبرگشت BIND، ماشین
وضعیت DNSSEC، ایدمپوتنسی قالب GitHub Pages و ذخیره‌نشدن توکن خام.

## گام بعدی (نقشه راه)

1. اتصال `apply_changes` به PowerDNS HTTP API و ثبت SOA/rectify واقعی.
2. کارگر `verify_ns` و `verify_ds` (river/Celery) روی ناحیه‌های pending.
3. `point-stats` برای پر کردن `point.usage.hourly` از dnstap.
4. احراز هویت واقعی اعضا، TOTP و کدهای بازیابی.
5. صورتحساب، سهمیه طرح و اتصال به `cloud.core.service.instance`.
6. قالب‌های Vercel/Netlify و ایمیل سازمانی.

## محیط آزمون محلی (Docker)

برای دیدن بدون نصب روی سرور:

```bash
docker network create pointnet
docker run -d --name point-pg --network pointnet \
  -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres postgres:16-alpine
KEY=$(python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())" | tee /tmp/point_fernet)

ADDONS="<repo>/Bodoo/extra-addons"

docker run --rm --network pointnet -e HOST=point-pg -e USER=odoo -e PASSWORD=odoo \
  -e CLOUD_SECRET_MANAGER_FERNET_KEY="$KEY" -v "$ADDONS:/mnt/extra-addons:ro" \
  odoo:19 odoo -d pointdb -i point_dns \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons --stop-after-init

docker run -d --name point-odoo-srv --network pointnet -p 8069:8069 -e HOST=point-pg -e USER=odoo \
  -e PASSWORD=odoo -e CLOUD_SECRET_MANAGER_FERNET_KEY="$KEY" \
  -v "$ADDONS:/mnt/extra-addons:ro" \
  odoo:19 odoo -d pointdb --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --db-filter='^pointdb$'
```

سپس با ورود فرم (`admin` پس از `odoo shell` و ثبت رمز) صفحه `/point` دیده می‌شود.
نکته: پس از ری‌استارت ماشین، کانتینرها از بین می‌روند و باید همین دستورها دوباره اجرا شوند؛
کلید FERNET باید بین نصب و اجرای سرور یکی باشد.

## دامنهٔ فاز ۰ بر پایهٔ bukuچهٔ راهنماي V4 (`point-handbook_v4.html`)

این افزونه فقط **فاز ۰ = نقطهٔ DNS** را پیاده میکند (گیت G0). نقشهٔ راه کامل
خانوادهٔ محصولات Point: فاز ۰ DNS · فاز ۱ لبه (پراکسی/CDN/WAF) · فاز ۲ ریزبان
(DoH/DoT) · فاز ۳/۴ دسترسی (ZTNA) · فاز ۵ امضای پس‌کوانتومی.

* **منوی کنارِ پنل** (زیر شاخهٔ «نقطه» در `burna_layout`) فقط فاز ۰ را دارد:
  ناحیه‌ها و رکوردها · ناحیه جدید · تیم · توکن‌های API · امنیت و رمزنگاری ·
  پیشخوان کارکنان (فقط `group_system`).
* **قاعدهٔ UI کتابچه**: قابلیت‌های فازهای بعد **حذف نشده، بلکه با برچسب فاز
  غیرفعال می‌شوند** — کارت‌های قالب Vercel/Netlify/ایمیل سازمانی
  («فاز ۱+ · بهزودی») و ردیف‌های TLS لبه/DoH/CBOM/امضای PQ در صفحهٔ
  «امنیت و رمزنگاری».
* **کارت «سیاست رمزنگاری» (تنها نمایش، داخلی)**: پنل و API و همگامسازی و ارسال
  پشتیبان با X25519MLKEM768 (⚛)، DNSSEC کلاسیک ECDSA P-256 algorithm 13.
  نشان ⚛ فقط بر اساس گروه توافقشدهٔ واقعی (از لاگ، نه از تنظیمات) معنا دارد.

نکتهٔ گیت G0 (زیرساخت، خارج از این UI): حدود ۲۰ ناحیهٔ فعال و ۱۰۰٪ نشستهای
پنل/API/همگامسازی روی X25519MLKEM768.

## موتور DNS (نمایشی یا PowerDNS واقعی)

به‌طور پیش‌فرض نوشتن‌ها بی‌اثر روی بیرون هستند («موتور نمایشی») و فقط در Odoo
و لاگ ثبت می‌شوند. برای اتصال به یک PowerDNS Authoritative واقعی:

1. در «امنیت و رمزنگاری» (فقط کارکنان) آدرس API و کلید `X-API-Key` را ذخیره
   کنید (`ir.config_parameter`: `point_dns.pdns_base_url` / `point_dns.pdns_api_key`).
2. در تب «تنظیمات» هر ناحیه، «موتور DNS» را روی PowerDNS بگذارید و
   «آزمایش اتصال» را بزنید.
3. از آن پس ساخت ناحیه، تغییر رکوردها (batch)، حذف/بازگردانی و DNSSEC از طریق
   REST API موتور انجام می‌شود؛ SOA و rectify و کلیدها مال PowerDNS هستند.

شرط دسترسی: API موتور باید از این سرور قابل دسترسی باشد. نمونهٔ فاز ۰ فعلی روی
`noghte-dns-01` تنها روی `127.0.0.1:8081` گوش می‌دهد و نیازمند شبکهٔ خصوصی یا
تونل است.
