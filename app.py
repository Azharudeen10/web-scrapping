import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random

LIST_URL = "https://rera.odisha.gov.in/projects/project-list"


def get_projects_with_details():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(LIST_URL)
        time.sleep(5)  # allow page to fully load

        projects = []
        # we'll process indexes 0–5
        for idx in range(6):
            try:
                # re-find the buttons each time to avoid stale references
                buttons = driver.find_elements(
                    By.XPATH,
                    '//a[contains(@class,"btn-primary") and contains(.,"View Details")]'
                )
                btn = buttons[idx]

                # scroll & click via JS
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(4)  # wait for details page to load

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # --- Project Overview ---
                rera_no = proj_name = None
                for div in soup.select('div.details-project.ms-3'):
                    lbl = div.find('label', class_='label-control', string=True)
                    val = div.find('strong')
                    if not lbl or not val:
                        continue
                    txt = lbl.string.strip()
                    if txt == "RERA Regd. No.":
                        rera_no = val.get_text(strip=True)
                    elif txt == "Project Name":
                        proj_name = val.get_text(strip=True)

                # --- Promoter Details ---
                # click the “Promoter Details” tab by its link text
                prom_tab = driver.find_element(
                    By.XPATH,
                    "//a[normalize-space(.)='Promoter Details']"
                )
                driver.execute_script("arguments[0].click();", prom_tab)
                time.sleep(2)  # wait for tab content

                soup2 = BeautifulSoup(driver.page_source, 'html.parser')
                def scrape_field(label_text):
                    lbl = soup2.find('label', class_='label-control', string=label_text)
                    if lbl:
                        strong = lbl.find_next_sibling('strong')
                        return strong.get_text(strip=True) if strong else None
                    return None

                company_name = scrape_field("Company Name")
                office_addr   = scrape_field("Registered Office Address")
                gst_no        = scrape_field("GST No.")

                projects.append({
                    "Rera Regd. No.":    rera_no,
                    "Project Name":      proj_name,
                    "Company Name":      company_name,
                    "Registered Office": office_addr,
                    "GST No.":           gst_no
                })

                # go back and ensure list reload
                driver.back()
                time.sleep(5)  # give list page time to re-render

            except Exception as e:
                projects.append({"Error": f"Failed scraping project #{idx+1}: {e}"})
                # try to get back to list page if not already
                try:
                    driver.back()
                    time.sleep(3)
                except:
                    pass

        return projects

    except Exception as e:
        return [{"Error": str(e)}]

    finally:
        driver.quit()


# ---- Streamlit UI ----
st.title("🏗️ Odisha RERA: Project Details")

if "project_details" not in st.session_state:
    st.session_state.project_details = []

if st.button("🔍 Fetch Project Details"):
    with st.spinner("Scraping project overview & promoter details..."):
        st.session_state.project_details = get_projects_with_details()

if st.session_state.project_details:
    st.subheader("First 6 Registered Projects")
    for idx, proj in enumerate(st.session_state.project_details, start=1):
        if "Error" in proj:
            st.error(f"{idx}. {proj['Error']}")
        else:
            st.markdown(f"**{idx}. {proj['Project Name'] or '–'}**")
            st.write(f"- **Rera Regd. No.:** {proj.get('Rera Regd. No.', '–')}")
            st.write(f"- **Company Name:** {proj.get('Company Name', '–')}")
            st.write(f"- **Registered Office:** {proj.get('Registered Office', '–')}")
            st.write(f"- **GST No.:** {proj.get('GST No.', '–')}")
            st.write("---")