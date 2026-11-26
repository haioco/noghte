# Noghte SASE / HaioSASE — مدارک سرمایه‌گذاری و پیشنهاد

کپی مدارک مرتبط با محصول SASE نقطه (هايSASE / اپلیکیشن اندروید نقطه) از پوشهٔ
`~/Documents/mine/Haio-Forever/Funding/NoghteSASE/`. نسخهٔ **اصلی** همان‌جا
می‌ماند؛ این‌ها برای ادامهٔ کار در ریپوی نقطه منتقل شده‌اند (کپی).

| فایل | چیست |
|---|---|
| `noghte-landing.html` | صفحهٔ فرود نقطه (SASE) |
| `PointQ_LandingPage.html` | صفحهٔ فرود PointQ |
| `SASE-Compliance-Report.html` | گزارش انطباق SASE |
| `A10-Proposal-V24-Companies-FILLED.html` | پیشنهاد A10 نسخهٔ FILLED (HTML) |
| `noghte-proposal-filled.docx` | پیشنهاد نقطه (پرشده) |
| `A10-Proposal-V24-Companies-FILLED.docx` | پیشنهاد A10 (پرشده) |
| `A10-Proposal-V24- companies.docx` | پیشنهاد A10 (خام) |
| `sample.docx` | نمونهٔ قالب سند |
| `تحلیل معماری SASE و ارزیابی پروژه HaioBypass.html` | تحلیل معماری + ارزیابی |
| `دیتاشیت فنی HaioSASE — سامانه ارتباط امن پساکوانتومی.html` | دیتاشیت فنی |
| `معماری HaioSASE-PQC - راهکار SASE با رمزنگاری پساکوانتومی.html` | معماری PQC |

## نسخه‌های بازبینی‌شده (منتقل‌شده از ریشهٔ ریپو)

| فایل | چیست |
|---|---|
| `noghte-proposal-revised.docx` / `.pdf` | پیشنهاد بازبینی‌شده پس از نظرهای بازبین |
| `noghte-supplementary-answers.docx` / `.pdf` | سند پاسخ‌ها به پرسش‌های تکمیلی بازبین |
| `build_proposal.py` | سازندهٔ `noghte-proposal-revised.docx` |
| `build_supplementary.py` | سازندهٔ `noghte-supplementary-answers.docx` |
| `docx_helpers.py` | توابع مشترک قالب‌بندی DOCX (RTL، جدول، رنگ) |

اجرا از ریشهٔ ریپو (نهکز به `docs/sase/`):

```bash
python3 docs/sase/build_proposal.py       # خروجی: docs/sase/noghte-proposal-revised.docx
python3 docs/sase/build_supplementary.py  # خروجی: docs/sase/noghte-supplementary-answers.docx
```

نیاز به `python-docx` دارد؛ نشان سند از `docs/noghte-emblem.png` خوانده می‌شود.

نکته: `noghte-proposal-filled.docx` اینجا **کپی از `Funding/NoghteSASE`** است و
با فایل هم‌نام در ریشهٔ ریپو (نسخهٔ ۳ اکتبر) محتوای متفاوتی دارد؛ هر دو نگه
داشته شده‌اند.

## فایل‌های حجیم (کپی نشده — نسخهٔ اصلی در Funding/NoghteSASE/)

* `Sovereign_SASE_Architecture.pptx` (~۱۵ مگابایت)
* `HAIO-PQC-SASE(1).png` و `HAIO-PQC-SASE(2).png` (~۱٫۷ مگابایت هرکدام)

این‌ها برای سبک نگه داشتن ریپو کپی نشده‌اند؛ در صورت نیاز از مسیر اصلی
استفاده شود.

## مرتبط

* `../point-handbook_v4.html` — فازهای ۲ تا ۵ (Resolver/Access/PQ) همین خانواده.
* `../PLAN-SASE-FULL.md`, `../PLAN-SASE-CLIENT-ONLY.md` (ریشهٔ ریپو) — نقشهٔ SASE.
* اپ اندروید نقطه: `../app/` و سند تست کاربر نهایی `../docs/end-user-test-v1.2.5.md`.