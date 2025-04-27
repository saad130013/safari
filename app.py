
import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# إنشاء أو الاتصال بقاعدة بيانات بسيطة
conn = sqlite3.connect('statements.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        year INTEGER,
        critical_areas INTEGER,
        medium_risk_areas INTEGER,
        general_areas INTEGER,
        total_cost REAL,
        vat REAL,
        total_with_vat REAL
    )
''')
conn.commit()

st.set_page_config(page_title="نظام مستخلصات سفاري", layout="wide", page_icon="📄")
st.title("📄 نظام إدارة المستخلصات الشهرية لشركة سفاري")
st.caption("نظام ذكي لتحليل المستخلصات الشهرية، عرض الأداء، والمقارنة بين الشهور 📊")

# رفع ملف
uploaded_file = st.file_uploader("📂 ارفع ملف المستخلص (Excel)", type=["xlsx"])

if uploaded_file:
    with st.form("form"):
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("📅 اختر الشهر", ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"])
        with col2:
            year = st.number_input("📆 ادخل السنة", min_value=2020, max_value=2100, value=2025)
        submitted = st.form_submit_button("📥 تحليل وحفظ المستخلص")

    if submitted:
        # قراءة الشيت المناسب
        xl = pd.ExcelFile(uploaded_file)
        service_sheet = xl.parse("قيمة الخدمة")

        # استخراج البيانات
        try:
            critical_areas = int(service_sheet.iloc[2, 2])
            medium_risk_areas = int(service_sheet.iloc[3, 2])
            general_areas = int(service_sheet.iloc[4, 2])
            total_cost = float(service_sheet.iloc[2, 11] + service_sheet.iloc[3, 11] + service_sheet.iloc[4, 11])
            vat = float(service_sheet.iloc[2, 12] + service_sheet.iloc[3, 12] + service_sheet.iloc[4, 12])
            total_with_vat = float(service_sheet.iloc[2, 13] + service_sheet.iloc[3, 13] + service_sheet.iloc[4, 13])

            cursor.execute('''
                INSERT INTO service_statements (month, year, critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (month, year, critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat))
            conn.commit()
            st.success("✅ تم حفظ المستخلص وتحليله بنجاح!")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء التحليل: {e}")

# عرض الداشبورد
st.header("📊 مقارنة وتحليل المستخلصات الشهرية")
data = pd.read_sql_query("SELECT * FROM service_statements", conn)
if not data.empty:
    st.subheader("📋 جدول البيانات")
    st.dataframe(data, use_container_width=True)

    st.subheader("📈 الرسم البياني لتطور إجمالي الفواتير")
    fig = px.bar(data, x='month', y='total_with_vat', color='month', text_auto=True,
                 labels={'total_with_vat': 'إجمالي الفاتورة (مع الضريبة)'},
                 title="تطور إجمالي قيمة المستخلصات شهريًا")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📉 مقارنة الفرق بين الشهور")
    data_sorted = data.sort_values(['year', 'month'])
    data_sorted['التغير الشهري (%)'] = data_sorted['total_with_vat'].pct_change() * 100
    st.dataframe(data_sorted[['month', 'year', 'total_with_vat', 'التغير الشهري (%)']].round(2), use_container_width=True)

    with st.expander("⬇️ تحميل البيانات الكاملة"):
        csv = data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل CSV", data=csv, file_name='service_statements.csv', mime='text/csv')
else:
    st.info("ℹ️ لا توجد بيانات مضافة بعد. يرجى رفع أول مستخلص.")
