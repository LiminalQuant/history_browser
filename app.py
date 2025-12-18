import sqlite3
import pandas as pd
import streamlit as st
import base64
from io import BytesIO
import tempfile
import os

def generate_excel_download_link(df):
    towrite = BytesIO()
    df.to_excel(towrite, index=False)
    towrite.seek(0)

    b64 = base64.b64encode(towrite.read()).decode()
    href = f'''
    <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"
       download="browser_history.xlsx">
       Скачать Excel
    </a>
    '''
    st.markdown(href, unsafe_allow_html=True)


st.set_page_config(page_title='History')
st.title('Вскрываем историю браузера')
st.subheader('Добавьте файл History (Chrome / Edge)')

uploaded_file = st.file_uploader('Выберите файл history', type=['db', 'sqlite'])

if uploaded_file:
    # --- сохраняем во временный файл ---
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        con = sqlite3.connect(tmp_path)

        query = """
        SELECT
            url,
            title,
            visit_count,
            datetime(last_visit_time / 1000000 +
                     (strftime('%s', '1601-01-01')),
                     'unixepoch', 'localtime') AS visit_time
        FROM urls
        """

        df = pd.read_sql(query, con)

    finally:
        con.close()
        os.remove(tmp_path)

    # --- нормализация ---
    df = df.rename(columns={
        "visit_time": "Дата",
        "url": "Адрес",
        "title": "Имя запроса",
        "visit_count": "Посещений страницы"
    })

    df["Дата"] = pd.to_datetime(df["Дата"], errors="coerce")
    df["Месяц"] = df["Дата"].dt.month
    df["Год"] = df["Дата"].dt.year

    st.success(f"Загружено записей: {len(df)}")

    if st.checkbox('Показать таблицу'):
        st.dataframe(df)

    if st.checkbox('Сформировать Excel'):
        generate_excel_download_link(df)
