# نقطه — سند تأیید و شواهد

آخرین به‌روزرسانی: ۲۶ نوامبر ۲۰۲۶

## ۱) آزمون‌ها و بررسی‌های ایستا (افزونهٔ point_dns)

| بررسی | نتیجه |
|---|---|
| `odoo --test-tags /point_dns` | ۰ خطا، ۰ شکست از ۲۲ آزمون (`test_point.py` ۱۰ + `test_pdns.py` ۱۲) |
| `ruff check` | پاس |
| `python3 -m compileall` | پاس |

## ۲) محیط آزمون محلی (Docker)

ایمیج‌های `odoo:19` و `postgres:16-alpine` به‌صورت محلی موجودند:

```bash
docker network create pointnet
docker run -d --name point-pg --network pointnet \
  -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres \
  postgres:16-alpine
KEY=$(python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
echo "$KEY" > /tmp/opencode/fernet

# نصب (env لازم است؛ entrypoint به --db_host توجه نمی‌کند)
docker run --rm --network pointnet -e HOST=point-pg -e USER=odoo -e PASSWORD=odoo \
  -e CLOUD_SECRET_MANAGER_FERNET_KEY="$KEY" \
  -v "<پوشهٔ clouda>/Bodoo/extra-addons:/mnt/extra-addons:ro" \
  odoo:19 odoo -d pointdb -i point_dns \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --without-demo=all --stop-after-init --log-level=warn

# سرویس
docker run -d --name point-odoo-srv --network pointnet -p 8069:8069 \
  -e HOST=point-pg -e USER=odoo -e PASSWORD=odoo \
  -e CLOUD_SECRET_MANAGER_FERNET_KEY="$KEY" \
  -v "<پوشهٔ clouda>/Bodoo/extra-addons:/mnt/extra-addons:ro" \
  odoo:19 odoo -d pointdb \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --db-filter='^pointdb$'
```

نکته‌های محیط:

* کلید fernet باید بین نصب و سرویس **یکی** باشد (`/tmp/opencode/fernet`).
* پس از تغییر کد: `docker run ... -u point_dns` برای ارتقا و
  `docker restart point-odoo-srv` برای سرویس.
* `burna_layout` مسیرهای JSON-RPC را برای کاربر ناشناس بسته است؛ ورود با فرم
  انجام می‌شود:

```bash
curl -s -c /tmp/opencode/cj.txt "http://localhost:8069/web/login?db=pointdb" > page.html
CSRF=$(grep -oP '<input[^>]*name="csrf_token"[^>]*' page.html | grep -oP '(?<=value=")\K[^"]*')
curl -s -b /tmp/opencode/cj.txt -c /tmp/opencode/cj.txt \
  -d "db=pointdb&login=admin&password=admin&csrf_token=$CSRF&redirect=/point" \
  "http://localhost:8069/web/login"
```

* نوشتن از `odoo shell` باید `env.cr.commit()` داشته باشد.
* CSRF در QWeb به‌ترتیب رندر می‌شود و `value` آخر است؛ الگوی
  `(?<=name="csrf_token" value=")` **کار نمی‌کند**.

## ۳) صفحه‌ها و جریان‌های تأییدشده (پنل)

* همهٔ صفحه‌ها ۲۰۰: `/point`، `/point/zones`، `/point/zones/new`، شش تب جزئیات
  ناحیه (رکوردها/NS/DNSSEC/آمار/تاریخچه/تنظیمات)، `/point/zones/<id>/import`،
  `/point/zones/<id>/templates`، `/templates/github-pages`،
  `/point/settings/{team,tokens,security}`، `/point/staff`.
* ساخت ناحیه با پروفایل وب، ذخیرهٔ اتمیک پیش‌نویس رکوردها، واردسازی BIND
  (پیش‌نمایش + ثبت)، تأیید NS → فعال، چرخهٔ DNSSEC (awaiting_ds → active)،
  تعلیق/رفع تعلیق کارکنان، ساخت توکن (نمایش یک‌بار مقدار خام)، دعوت عضو.
* قالب GitHub Pages: پیش‌نمایش، اعمال (۴ A + ۴ AAAA + CNAME)، اعمال دوم
  بدون تغییر (idempotent).
* REST API (`/api/point/v1` با Bearer): healthz، `/me`، zones/PUT/DELETE، stats؛
  توکن اشتباه ۴۰۱ با `application/problem+json`؛ جداسازی مستأجرها تأیید شد.
* خروجی BIND درست: `$ORIGIN` با نقطهٔ آخر، TXT کوتیشن‌شده، MX/CNAME نرمال‌شده.

## ۴) سرویس زندهٔ noghte-dns-01 (۹۴.۱۸۲.۱۷۲.۹۶)

سخت‌سازی با `deploy/point-dns/harden.sh` اعمال شد (PR #3):

* فقط upstream `127.0.0.1:5300`؛ CHAOS و ANY → REFUSED (با مقدار عددی ۳ و ۲۵۵)؛
  UPDATE → NOTIMP؛ محدودیت‌های نرخ/TCP بدون تغییر.
* dnsdist 1.8.3: `DNSClass.CH` و `DNSQType.ANY` مقدار nil دارند و
  `--check-config` با آدرس‌های سمبلیک شکست می‌خورد → عدد لازم است.
* تأیید زنده: `www.probe A` → ۹۴.۱۸۲.۱۷۲.۹۶؛ google.com/youtube.com → REFUSED؛
  ANY → REFUSED؛ `id.server CHAOS TXT` → REFUSED؛ SOA و `+dnssec` → NOERROR؛
  `nsupdate` → NOTIMP.
* تصحیح ادعای قبلی: سرور هرگز recurse نکرد؛ پاسخ‌های NOERROR بیرونی ناشی از
  رهگیری مسیر پاسخ روی شبکهٔ محلی workstation بود، نه سرور.

یافته‌های باز:

1. پس از ساخت/ساخت مجدد ناحیه، `pdns_control purge` کافی نیست و کش منفی فقط با
   `systemctl restart pdns` پاک می‌شود (`install.sh` اصلاح شد).
2. امضاکردن RRSIG روی pdns ۴.۸.۳ + gsql اتفاق نمی‌افتد: DNSKEY و DS منتشر
   می‌شوند (keytag ۱۰۲۷۳، alg ۱۳) ولی `PUT /rectify` هیچ RRSIG نمی‌سازد؛
   `/dnssec` روی ۴.۸.۳ → ۴۰۴. نقشه: قبل از بتا ریپوی PowerDNS 5.0 پین شود و
   DNSSEC دوباره سنجیده شود.
3. API موتور فقط روی `127.0.0.1:8081` داخل VM است و VM NIC خصوصی ندارد →
   برای اتصال واقعی پنل به شبکهٔ خصوصی/تونل/محدودسازی IP نیاز است.

## ۵) مشکلات شناخته‌شده

* `/console` در همین دیتابیس آزمون ۵۰۰ می‌دهد (`KeyError: 'burna.ticket'`) چون
  `burna_tickets` نصب نیست؛ قبلی است و به نقطه ربطی ندارد.

## ۶) پیوندها

* تسک برد (سخت‌سازی + اتصال موتور): `01c9705f-550b-40c7-90ff-7360187cbd5b`
  مسائل haioco/noghte#2
* تسک برد (مهاجرت مستندات): `91aec73e-3381-4a88-8d1f-f5708f57677b`
  مسائل haioco/noghte#4
* PR سخت‌سازی: https://github.com/haioco/noghte/pull/3 (شاخهٔ `fix/point-dns-harden`)