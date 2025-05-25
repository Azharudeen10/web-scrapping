import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd

LIST_URL = "https://rera.odisha.gov.in/projects/project-list"

def get_projects_with_details(progress_callback=None):
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
        time.sleep(5)  # let the list page fully load

        projects = []
        total = 6
        if progress_callback:
            progress_callback(0)
        for idx in range(total):
            try:
                buttons = driver.find_elements(
                    By.XPATH,
                    '//a[contains(@class,"btn-primary") and contains(.,"View Details")]'
                )
                btn = buttons[idx]
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(4)  # wait for details

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                rera_no = proj_name = "—"
                for div in soup.select('div.details-project.ms-3'):
                    lbl = div.find('label', class_='label-control', string=True)
                    val = div.find('strong')
                    if not lbl:
                        continue
                    label_text = lbl.string.strip()
                    value = val.get_text(strip=True) if val else "—"
                    if label_text == "RERA Regd. No.":
                        rera_no = value
                    elif label_text == "Project Name":
                        proj_name = value

                try:
                    prom_tab = driver.find_element(
                        By.XPATH, "//a[normalize-space(.)='Promoter Details']"
                    )
                    driver.execute_script("arguments[0].click();", prom_tab)
                    time.sleep(2)
                    soup2 = BeautifulSoup(driver.page_source, 'html.parser')
                except:
                    soup2 = soup

                def scrape_field(label_text):
                    lbl = soup2.find('label', class_='label-control', string=label_text)
                    if lbl:
                        strong = lbl.find_next_sibling('strong')
                        if strong and strong.get_text(strip=True):
                            return strong.get_text(strip=True)
                        sib = lbl.find_next_sibling()
                        if sib and sib.get_text(strip=True):
                            return sib.get_text(strip=True)
                    return "—"

                promoter_name = scrape_field("Company Name")
                promoter_address = scrape_field("Registered Office Address")
                if promoter_name == "—":
                    promoter_name = scrape_field("Propietory Name")
                if promoter_address == "—":
                    promoter_address = scrape_field("Permanent Address")
                gst_no = scrape_field("GST No.")

                projects.append({
                    "Project Name": proj_name,
                    "RERA Regd. No.": rera_no,
                    "Promoter Name": promoter_name,
                    "Promoter Address": promoter_address,
                    "GST No.": gst_no
                })
                driver.back()
                time.sleep(4)

            except Exception as e:
                projects.append({"Error": f"Project #{idx+1} scrape failed: {e}"})
                try:
                    driver.back()
                    time.sleep(2)
                except:
                    pass

            if progress_callback:
                progress_callback((idx+1)/total)

        return projects

    except Exception as e:
        return [{"Error": str(e)}]

    finally:
        driver.quit()

# ---- Streamlit UI ----
st.title("🏗️ Odisha RERA: Project Details")

if 'project_details' not in st.session_state:
    st.session_state.project_details = []

if st.button("🔍 Fetch Project Details"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    def update_progress(pct):
        progress_bar.progress(pct)
        status_text.text(f"Progress: {int(pct*100)}%")

    with st.spinner("Scraping project overview & promoter details..."):
        st.session_state.project_details = get_projects_with_details(progress_callback=update_progress)
    status_text.text("Scrape complete!")
    st.balloons()

if st.session_state.project_details:
    st.subheader("Projects Registered")
    for idx, proj in enumerate(st.session_state.project_details, start=1):
        if "Error" in proj:
            st.error(f"{idx}. {proj['Error']}")
        else:
            st.markdown(f"**{idx}. {proj['Project Name']}**")
            st.write(f"- **RERA Regd. No.:** {proj['RERA Regd. No.']}")
            st.write(f"- **Promoter Name:** {proj['Promoter Name']}")
            st.write(f"- **Promoter Address:** {proj['Promoter Address']}")
            st.write(f"- **GST No.:** {proj['GST No.']}")
            st.write("---")

    # CSV Download
    df = pd.DataFrame(st.session_state.project_details)
    csv_bytes = df.to_csv(index=False).encode('utf-8')

    download_clicked = st.download_button(
        label="📥 Download as CSV",
        data=csv_bytes,
        file_name='rera_projects.csv',
        mime='text/csv'
    )

    if download_clicked:
        st.balloons()
        st.success("CSV file downloaded successfully!")
