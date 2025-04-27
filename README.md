# 📄 Safari Statement Management System

نظام ذكي لإدارة وتحليل مستخلصات شركة سفاري شهريًا.

## الميزات:
- رفع ملف Excel لكل شهر.
- استخراج معلومات الأداء والتكاليف تلقائيًا.
- تخزين البيانات في قاعدة بيانات SQLite.
- عرض Dashboard تفاعلي لتحليل الشهور ومقارنتها.
- تحميل النتائج كملف CSV.

## طريقة التشغيل:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## المتطلبات:
- Python 3.8+
- مكتبات: streamlit, pandas, openpyxl, plotly
