# یکپارچه‌سازی نقطه با کلودا (Odoo)

نقطه (Point DNS) به‌صورت **افزونهٔ Odoo 19** داخل پلتفرم کلودا پیاده شده است، نه
به‌صورت اپ جداگاه. این سند می‌گوید کد کجاست، وضعیت گیت چگونه است و کار چگونه
ادامه پیدا می‌کند.

## مکان کد

| چه | کجا |
|---|---|
| افزونهٔ پنل نقطه | `~/Documents/mine/Haio-Forever/بازارگاه هوش مصنوعی/clouda/Bodoo/extra-addons/point_dns/` |
| زیرمنوی نوار کناری | همان ریپو، `clouda/Bodoo/extra-addons/burna_layout/` |
| سرویس زندهٔ DNS | VM `noghte-dns-01` (94.182.172.96) — اسکریپت‌های نصب و سخت‌سازی در `deploy/point-dns/` همین ریپو |

ریپوی کلودا remote `git@github.com:haioco/...` (clouda) و افزونه از کامیت
`fc391cb8 feat(odoo): add point_dns addon for point.ir DNS management` در گیت
**ردیف‌شده** است؛ تغییرات پس از آن هنوز کامیت نشده‌اند.

## وابستگی‌ها و پیاده‌سازی

* پوستهٔ پنل مشتری: `burna_layout.burna_panel_base` + قالب `burna.menu.item`
* نوع رکورد DNS: `cloud.dns.record.type` از `haio_domain_cso` (افزونهٔ نقطه
  رکوردهای SRV/CAA/PTR را اضافه می‌کند)
* فونت‌ها: `clouda_web_assets` (Vazirmatn)
* موتور DNS: `mock` پیش‌فرض؛ `pdns` از طریق سرویس `services/pdns_client.py`
  (PowerDNS Authoritative REST API)

## زیرمنوی «نقطه» در نوار کناری (burna_layout)

افزونهٔ `burna_layout` تغییر کرده تا شاخه‌های دارای فرزند به‌جای فهرست صاف،
**زیرمنوی باز/بسته‌شو** باشند:

* `views/shared_sidebar.xml` — تمپلیت `menu_icon` (اولویت: `icon_svg_url` →
  ایموجی `icon` → `route_icon`) و شاخهٔ `burna-nav-group` + پنل `burna-nav-sub`
  که فقط وقتی مسیر فعلی داخل شاخه باشد خودکار باز می‌شود.
* `static/src/css/console.css` — کلاس‌های `.burna-nav-group` / `.burna-nav-sub`
* `static/src/js/console.js` — باز/بسته کردن با کلیک
* `models/burna_menu_item.py` — `permissions` حالا شناسهٔ کامل گروه
  (`group_system` یا `base.group_system`) را هم می‌پذیرد؛ عضویت از
  `user.sudo().group_ids & groups` بررسی می‌شود (نسخهٔ قبلی با `has_group`
  هیچ‌وقت مطابقت نمی‌کرد و «پیشخوان کارکنان» از همه پنهان بود).

زیرمنوی نقطه: داشبورد (`/point`)، ناحیه‌ها و رکوردها، ناحیه جدید، تیم، توکن‌های
API، امنیت و رمزنگاری، پیشخوان کارکنان (فقط `group_system`).

نکته: سایدبار فقط ریشه و فرزندان **مستقیم** را رندر می‌کند؛ همهٔ آیتم‌های نقطه
فرزندهٔ مستقیم ریشهٔ `route=/point` هستند.

## وضعیت گیت (۲۶ نوامبر ۲۰۲۶)

ریپوی کلودا روی شاخهٔ `feat/dc3-offsite-backup`. تغییرات کامیت‌نشدهٔ مرتبط با نقطه:

```
Bodoo/extra-addons/point_dns/CHANGELOG.md
Bodoo/extra-addons/point_dns/README.md
Bodoo/extra-addons/point_dns/controllers/portal.py
Bodoo/extra-addons/point_dns/data/point_data.xml
Bodoo/extra-addons/point_dns/models/point_rrset.py
Bodoo/extra-addons/point_dns/models/point_zone.py
Bodoo/extra-addons/point_dns/services/__init__.py
Bodoo/extra-addons/point_dns/services/templates.py
Bodoo/extra-addons/point_dns/services/pdns_client.py        (جدید)
Bodoo/extra-addons/point_dns/tests/__init__.py
Bodoo/extra-addons/point_dns/tests/test_pdns.py             (جدید)
Bodoo/extra-addons/point_dns/views/point_zone_views.xml
Bodoo/extra-addons/point_dns/views/portal_settings.xml
Bodoo/extra-addons/point_dns/views/portal_templates.xml
Bodoo/extra-addons/point_dns/views/portal_zone.xml
Bodoo/extra-addons/burna_layout/CHANGELOG.md
Bodoo/extra-addons/burna_layout/models/burna_menu_item.py
Bodoo/extra-addons/burna_layout/static/src/css/console.css
Bodoo/extra-addons/burna_layout/static/src/js/console.js
Bodoo/extra-addons/burna_layout/views/shared_sidebar.xml
```

قانون کاری ریپوی کلودا (AGENTS.md): کار روی شاخهٔ جدا و MR؛ هرگز مستقیم روی
`main`. تا زمانی از کاربر تأیید نشود، کامیت نمی‌کنیم.

## دسترسی به موتور PowerDNS (بلوکر جاری)

API موتور روی VM فقط روی `127.0.0.1:8081` گوش می‌دهد و VM کارت شبکهٔ خصوصی
ندارد. پنل Odoo که جایی دیگر اجرا می‌شود به آن دسترسی ندارد. گزینه‌های عملی:

1. bind روی IP عمومی با `webserver-allow-from` محدود به IP پنل + کلید قوی، یا
2. تونل SSH/VPN بین پنل و موتور, یا
3. هم‌مکان کردن پنل و موتور روی یک شبکه

تنظیمات در پنل: «امنیت و رمزنگاری» → کارت «موتور PowerDNS» (فقط کارکنان) که
مقادیر را در `ir.config_parameter` با کلیدهای `point_dns.pdns_base_url` و
`point_dns.pdns_api_key` ذخیره می‌کند، و کارت «موتور DNS» در تب تنظیمات هر
ناحیه (انتخاب `mock`/`pdns` + «آزمایش اتصال»).

## ادامهٔ کار (پیشنهاد)

1. `docs/point-dns/odoo-addon-README.md` را برای وضعیت فعلی بخوانید (دامنهٔ نسخهٔ
   ۰٫۱، مسیرها، معماری، API).
2. محیط آزمون محلی Docker دستورهایش در
   `docs/point-dns/verification.md` آمده است.
3. قبل از هر تغییر روی کد افزونه، تسک روی برد موضوع («MCP تسک») باز شود
   (طبق قواعد `dev-tasks`).