
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# إعداد قاعدة البيانات
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
st.title("📄 نظام إدارة المستخلصات الشهرية لشركة سفاري - نسخة مصححة")
st.caption("نظام ذكي لتحليل المستخلصات وعرض المخالفات والغرامات بشكل دقيق")

uploaded_file = st.file_uploader("📂 ارفع ملف المستخلص (Excel)", type=["xlsx"])

if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)

    with st.form("form"):
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("📅 اختر الشهر", ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"])
        with col2:
            year = st.number_input("📆 ادخل السنة", min_value=2020, max_value=2100, value=2025)
        submitted = st.form_submit_button("📥 تحليل وحفظ المستخلص")

    if submitted:
        try:
            service_sheet = xl.parse("قيمة الخدمة")
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
            st.error(f"❌ خطأ أثناء قراءة شيت 'قيمة الخدمة': {e}")

    try:
        observers_df = xl.parse("مخالفات المراقبين")
    except:
        observers_df = pd.DataFrame()

    st.header("🕵️‍♂️ تفاصيل مخالفات المراقبين")
    if not observers_df.empty:
        try:
            selected_columns = observers_df[['التاريخ', 'الموقع', 'اسم الموقع', 'نوع المخالفة', 'مبلغ المخالفة']]
            st.dataframe(selected_columns, use_container_width=True)
            total_penalties = observers_df['مبلغ المخالفة'].sum()
            st.success(f"✅ إجمالي الغرامات: {total_penalties:,.2f} ريال سعودي")
        except Exception as e:
            st.error(f"⚠️ خطأ أثناء عرض تفاصيل المخالفات: {e}")
    else:
        st.info("ℹ️ لا توجد مخالفات مراقبين مضافة.")

else:
    st.info("📂 الرجاء رفع ملف مستخلص (Excel) لبدء التحليل.")
