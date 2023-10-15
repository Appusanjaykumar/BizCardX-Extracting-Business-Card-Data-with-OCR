import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import sqlite3
import io
import os

# Function to close the database connection
def close_connection(conn):
    if conn:
        conn.close()

# Database file path (use an absolute path)
db_file = 'C:/Users/ELCOT/Desktop/bizcard/cardsql.db'

# Create a connection to the database (this will create the file if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create a table for storing business card data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS BUSINESS_CARD (
        IMAGE_ID INTEGER PRIMARY KEY,
        NAME TEXT,
        DESIGNATION TEXT,
        COMPANY_NAME TEXT,
        CONTACT TEXT,
        EMAIL TEXT,
        WEBSITE TEXT,
        ADDRESS TEXT,
        PINCODE TEXT
    )
''')
conn.commit()

# Define a session state variable to store OCR data
if 'ocr_data' not in st.session_state:
    st.session_state.ocr_data = None

# Title
st.markdown("<h1 style='text-align: center; color: white;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

# Option menu
selected = option_menu(
    menu_title=None,
    options=["Image", "Delete", "Contact"],
    icons=["image", "trash", "at"],
    default_index=0,
    orientation="horizontal"
)

# Extracted data function
def extracted_text(result):
    ext_dic = {'Name': [], 'Designation': [], 'Company name': [], 'Contact': [], 'Email': [], 'Website': [],
               'Address': [], 'Pincode': []}

    ext_dic['Name'].append(result[0])
    ext_dic['Designation'].append(result[1])

    address_lines = []  # Create a list to store address lines

    for m in range(2, len(result)):
        if result[m].startswith('+') or (result[m].replace('-', '').isdigit() and '-' in result[m]):
            ext_dic['Contact'].append(result[m])

        elif '@' in result[m] and '.com' in result[m]:
            small = result[m].lower()
            ext_dic['Email'].append(small)

        elif 'www' in result[m] or 'WWW' in result[m] or 'wwW' in result[m]:
            small = result[m].lower()
            ext_dic['Website'].append(small)

        elif 'TamilNadu' in result[m] or 'Tamil Nadu' in result[m] or result[m].isdigit():
            ext_dic['Pincode'].append(result[m])

        elif re.match(r'^[A-Za-z]', result[m]):
            ext_dic['Company name'].append(result[m])

        else:
            removed_colon = re.sub(r'[,;]', '', result[m])
            address_lines.append(removed_colon)  # Append address lines to the list

    # Concatenate address lines into a single string
    full_address = ' '.join(address_lines)
    ext_dic['Address'].append(full_address)

    for key, value in ext_dic.items():
        if len(value) > 0:
            concatenated_string = ' '.join(value)
            ext_dic[key] = [concatenated_string]
        else:
            value = 'NA'
            ext_dic[key] = [value]

    return ext_dic

# Initialize selected_data variable
selected_data = None

if selected == "Image":
    image = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], key="image_uploader")

    if image is not None:
        input_image = Image.open(image)
        # Setting Image size
        st.image(input_image, width=350, caption='Uploaded Image')
        st.markdown(
            f'<style>.css-1aumxhk img {{ max-width: 300px; }}</style>',
            unsafe_allow_html=True
        )

        reader = easyocr.Reader(['en'], model_storage_directory=".")
        result = reader.readtext(np.array(input_image), detail=0)

        # Store OCR data in the session state
        st.session_state.ocr_data = extracted_text(result)

        # Creating dataframe
        ext_text = st.session_state.ocr_data
        df = pd.DataFrame(ext_text)
        st.dataframe(df)

        # Converting image into bytes
        image_bytes = io.BytesIO()
        input_image.save(image_bytes, format='PNG')
        image_data = image_bytes.getvalue()

        # Creating dictionary
        data = {"Image": [image_data]}
        df_1 = pd.DataFrame(data)
        concat_df = pd.concat([df, df_1], axis=1)

        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            selected = option_menu(
                menu_title=None,
                options=["Preview", "Delete"],
                icons=['file-earmark', 'trash'],
                default_index=0,
                orientation="horizontal"
            )

        ext_text = st.session_state.ocr_data
        df = pd.DataFrame(ext_text)

        if selected == "Preview":
            col_1, col_2 = st.columns([4, 4])
            with col_1:
                modified_n = st.text_input('Name', ext_text["Name"][0])
                modified_d = st.text_input('Designation', ext_text["Designation"][0])
                modified_c = st.text_input('Company name', ext_text["Company name"][0])
                modified_con = st.text_input('Mobile', ext_text["Contact"][0])
                concat_df["Name"], concat_df["Designation"], concat_df["Company name"], concat_df["Contact"] = modified_n, modified_d, modified_c, modified_con
            with col_2:
                modified_m = st.text_input('Email', ext_text["Email"][0])
                modified_w = st.text_input('Website', ext_text["Website"][0])
                modified_a = st.text_input('Address', ext_text["Address"][0])
                modified_p = st.text_input('Pincode', ext_text["Pincode"][0])
                concat_df["Email"], concat_df["Website"], concat_df["Address"], concat_df["Pincode"] = modified_m, modified_w, modified_a, modified_p

            col3, col4 = st.columns([4, 4])
            with col3:
                Preview = st.button("Preview modified text")
            with col4:
                Upload = st.button("Upload")
            if Preview:
                filtered_df = concat_df[
                    ['Name', 'Designation', 'Company name', 'Contact', 'Email', 'Website', 'Address', 'Pincode']]
                st.dataframe(filtered_df)
            else:
                pass

            if Upload:
                with st.spinner("In progress"):
                    A = "INSERT INTO BUSINESS_CARD (NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                    for index, i in concat_df.iterrows():
                        result_table = (i.iloc[0], i.iloc[1], i.iloc[2], i.iloc[3], i.iloc[4], i.iloc[5], i.iloc[6], i.iloc[7])
                        cursor.execute(A, result_table)
                        conn.commit()
                st.success('SUCCESSFULLY UPLOADED', icon="✅")
        else:
            col1, col2 = st.columns([4, 4])
            with col1:
                cursor.execute("SELECT IMAGE_ID, NAME, DESIGNATION FROM BUSINESS_CARD")
                results = cursor.fetchall()
                if not results:
                    st.warning("No data to delete.")
                else:
                    selected_data = st.multiselect("Select business cards to delete", [f"{result[0]} - {result[1]} ({result[2]})" for result in results])

            with col2:
                remove = st.button("Click here to delete")

if selected == "Delete":
    col1, col2 = st.columns(2)
    with col1:
        cursor.execute("SELECT IMAGE_ID, NAME, DESIGNATION FROM BUSINESS_CARD")
        results = cursor.fetchall()
        if not results:
            st.warning("No data to delete.")
        else:
            selected_data = st.multiselect("Select business cards to delete", [f"{result[0]} - {result[1]} ({result[2]})" for result in results])

    with col2:
        remove = st.button("Click here to delete")

    if selected_data and remove:
        for selected_card in selected_data:
            selected_data_id = int(selected_card.split(' - ')[0])
            cursor.execute("DELETE FROM BUSINESS_CARD WHERE IMAGE_ID = ?", (selected_data_id,))
            conn.commit()

        st.success('Selected business cards have been deleted', icon="✅")

if selected == "Contact":
    name = "Sanjay Kumar"
    mail = (f'{"Mail :"}  {"sanjaykumarsaravanan@gmail.com"}')
    description = "An Aspiring DATA-SCIENTIST..!"
    social_media = {
        "GITHUB": "https://github.com/Appusanjaykumar"}

    col1, col2 = st.columns(2)
    with col2:
        st.title('BizCardX: Extracting Business Card Data with OCR')
        st.write(
            "BizCardX is to automate and simplify the process of capturing and managing contact information from business cards, saving users time and effort. It is particularly useful for professionals who frequently attend networking events, conferences, and meetings where they receive numerous business cards that need to be converted into digital contacts.")
        st.write("---")
        st.subheader(mail)
    st.write("#")
    cols = st.columns(len(social_media))
    for index, (platform, link) in enumerate(social_media.items()):
        cols[index].write(f"[{platform}]({link})")

# Close the database connection at the end of the script
close_connection(conn)
