import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# إنشاء أو الاتصال بقاعدة بيانات بسيطة
def connect_db():
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
    return conn, cursor

# قراءة ورقة عمل معينة من ملف Excel
def read_sheet(xl, sheet_name):
    try:
        return xl.parse(sheet_name)
    except Exception as e:
        st.warning(f"⚠️ لم يتم العثور على الورقة '{sheet_name}': {e}")
        return pd.DataFrame()

# حساب الإجماليات
def calculate_totals(service_sheet):
    try:
        critical_areas = int(service_sheet.iloc[2, 2])
        medium_risk_areas = int(service_sheet.iloc[3, 2])
        general_areas = int(service_sheet.iloc[4, 2])
        total_cost = float(service_sheet.iloc[2, 11] + service_sheet.iloc[3, 11] + service_sheet.iloc[4, 11])
        vat = float(service_sheet.iloc[2, 12] + service_sheet.iloc[3, 12] + service_sheet.iloc[4, 12])
        total_with_vat = float(service_sheet.iloc[2, 13] + service_sheet.iloc[3, 13] + service_sheet.iloc[4, 13])
        return critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء حساب الإجماليات: {e}")
        return None, None, None, None, None, None

# عرض الرسوم البيانية
def display_charts(data):
    if not data.empty:
        st.subheader("📈 تطور إجمالي الفواتير")
        fig = px.bar(data, x='month', y='total_with_vat', color='month', text_auto=True,
                     labels={'total_with_vat': 'إجمالي الفاتورة (مع الضريبة)'},
                     title="تطور إجمالي قيمة المستخلصات شهريًا")
        fig.update_layout(yaxis_tickformat=",.2f")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📉 مقارنة الفرق بين الشهور")
        data_sorted = data.sort_values(['year', 'month'])
        data_sorted['التغير الشهري (%)'] = data_sorted['total_with_vat'].pct_change() * 100
        st.dataframe(data_sorted[['month', 'year', 'total_with_vat', 'التغير الشهري (%)']].round(2), use_container_width=True)

# الواجهة الرئيسية
def main():
    st.set_page_config(page_title="نظام مستخلصات سفاري", layout="wide", page_icon="📄")
    st.title("📄 نظام إدارة المستخلصات الشهرية لشركة سفاري")
    st.caption("نظام ذكي لتحليل المستخلصات الشهرية، عرض الأداء، والتفاصيل التفاعلية للمستهلكات والمعدات والمخالفات 📊")

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
            conn, cursor = connect_db()
            try:
                service_sheet = read_sheet(xl, "قيمة الخدمة")
                if service_sheet.empty:
                    st.error("❌ الورقة 'قيمة الخدمة' غير موجودة أو تحتوي على بيانات غير صحيحة.")
                    return

                critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat = calculate_totals(service_sheet)
                if None in [critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat]:
                    return

                cursor.execute('''
                    INSERT INTO service_statements (month, year, critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (month, year, critical_areas, medium_risk_areas, general_areas, total_cost, vat, total_with_vat))
                conn.commit()
                st.success("✅ تم حفظ المستخلص وتحليله بنجاح!")
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء المعالجة: {e}")
            finally:
                conn.close()

        # قراءة الأوراق الأخرى
        consumables_df = read_sheet(xl, "المستهلكات")
        equipment_df = read_sheet(xl, "المعدات والأجهزة")
        observers_df = read_sheet(xl, "مخالفات المراقبين")
        penalties_df = read_sheet(xl, "الغرامات")

        # عرض البيانات المحفوظة
        conn, cursor = connect_db()
        data = pd.read_sql_query("SELECT * FROM service_statements", conn)
        conn.close()

        if not data.empty:
            st.header("📊 مقارنة وتحليل المستخلصات الشهرية")
            st.subheader("📋 بيانات ملخصة")
            cols = st.columns(3)
            with cols[0]:
                st.metric("📅 الشهر", data.iloc[-1]['month'])
            with cols[1]:
                st.metric("📆 السنة", int(data.iloc[-1]['year']))
            with cols[2]:
                st.metric("💵 إجمالي مع الضريبة", f"{data.iloc[-1]['total_with_vat']:,.2f} ريال")

            col3, col4 = st.columns(2)
            with col3:
                st.metric("🧹 عدد المناطق الحرجة", int(data.iloc[-1]['critical_areas']))
            with col4:
                st.metric("🏢 عدد المناطق العامة", int(data.iloc[-1]['general_areas']))

            st.divider()
            display_charts(data)

            st.subheader("📂 تفاصيل إضافية")
            with st.expander("📦 المستهلكات"):
                if not consumables_df.empty:
                    st.dataframe(consumables_df, use_container_width=True)
                else:
                    st.info("لا توجد بيانات مستهلكات.")

            with st.expander("⚙️ المعدات والأجهزة"):
                if not equipment_df.empty:
                    st.dataframe(equipment_df, use_container_width=True)
                else:
                    st.info("لا توجد بيانات معدات وأجهزة.")

            with st.expander("🕵️‍♂️ مخالفات المراقبين"):
                if not observers_df.empty:
                    st.dataframe(observers_df, use_container_width=True)
                else:
                    st.info("لا توجد مخالفات مراقبين.")

            with st.expander("🚨 الغرامات"):
                if not penalties_df.empty:
                    st.dataframe(penalties_df, use_container_width=True)
                else:
                    st.info("لا توجد غرامات.")

            with st.expander("⬇️ تحميل البيانات الكاملة"):
                csv = data.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل CSV", data=csv, file_name='service_statements.csv', mime='text/csv')
        else:
            st.info("ℹ️ لا توجد بيانات مضافة بعد. يرجى رفع أول مستخلص.")
    else:
        st.info("📂 يرجى رفع ملف مستخلص (Excel) لبدء التحليل.")

if __name__ == "__main__":
    main()
