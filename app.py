import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def get_project_titles():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "https://rera.odisha.gov.in/projects/project-list"
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        titles = soup.find_all('h5', class_='card-title text-primary mb-0')
        return [title.get_text(strip=True) for title in titles]

    except Exception as e:
        return [f"❌ Error: {str(e)}"]

    finally:
        driver.quit()


# Streamlit UI
st.title("🏗️ Odisha RERA Project Titles")

# Setup session state for titles and show_more flag
if "project_titles" not in st.session_state:
    st.session_state.project_titles = []
if "show_more" not in st.session_state:
    st.session_state.show_more = False

# Fetch titles on button click
if st.button("🔍 Fetch Project Titles"):
    with st.spinner("Scraping project titles..."):
        st.session_state.project_titles = get_project_titles()
        st.session_state.show_more = False  # reset if fetching again

# Display titles
if st.session_state.project_titles:
    st.subheader("Projects Registered")
    for i, title in enumerate(st.session_state.project_titles[:6], 1):
        st.write(f"{i}. {title}")
