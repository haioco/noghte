# نقطه (Point) — مدارک فاز ۰

نقطه سرویس **میزبانی DNS معتبر** است (نسخهٔ ۰٫۱: مفهوم و رابط کاربری کامل +
اتصال اختیاری به موتور PowerDNS). کد پنل به‌صورت افزونهٔ Odoo داخل پلتفرم کلودا
زنده است؛ این پوشه نسخهٔ مرجع مدارک برای ادامهٔ کار در همین ریپو است.

| سند | چیست |
|---|---|
| `odoo-addon-README.md` | کپی مستند افزونهٔ `point_dns` (دامنه، نصب، مسیرها، معماری، API) |
| `odoo-addon-CHANGELOG.md` | کپی تغییرات افزونه |
| `odoo-integration.md` | محل کد، وضعیت گیت کلودا، تغییرات زیرمنوی `burna_layout`، بلوکر دسترسی به PowerDNS |
| `verification.md` | شواهد تأیید: آزمون‌ها، محیط Docker، جریان‌های پنل، تأیید زندهٔ سرور |

## اسناد طراحی

| سند | چیست |
|---|---|
| [`point-v1.1-plan.html`](point-v1.1-plan.html) | طرح اجرای نسخهٔ ۱ (Persian): مدل داده، API، صفحات پنل، قالب GitHub Pages، عملیات، نقشهٔ ۸ هفتگی |
| [`../point-handbook_v4.html`](../point-handbook_v4.html) | **سند اصلی محصول** — دفترچهٔ خانوادهٔ «نقطه»؛ فاز ۰ = Point DNS، فازهای بعد Edge/Resolver/Access/PQ |
| [`../reference/noghte-Point_Reference_Manuals.html`](../reference/noghte-Point_Reference_Manuals.html) | راهنماهای مرجع Point |

## استقرار و عملیات

`../deploy/point-dns/` — نصب تک‌نودی فاز ۰ (PowerDNS + dnsdist)، اسکریپت
سخت‌سازی و یافته‌های زنده.

## قواعد کار

* قوانین ریپو: `dev-tasks` (هر کار با تسک برد و مسائل گیت‌هاب)؛ نسخهٔ کد افزونه
  در کلودا با `AGENTS.md` (شاخه + MR، بدون کامیت مستقیم روی main).
* دامنهٔ فاز ۰ و «غیرفعال به‌جای پنهان» در `point-handbook_v4.html` تعریف شده.