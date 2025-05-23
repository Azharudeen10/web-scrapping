import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://rera.odisha.gov.in"

def fetch_project_rows(n):
    resp = requests.get(f"{BASE_URL}/projects/project-list")
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", attrs={"id": "projectList"})
    rows = table.tbody.find_all("tr")[:n]
    return rows

def parse_detail_page(detail_url):
    resp = requests.get(BASE_URL + detail_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    header = soup.find("div", class_="project-header")
    rera_no = header.find("span", text="Rera Regd. No").find_next_sibling("span").text.strip()
    proj_name = header.find("h3").text.strip()
    promo_tab = soup.find("div", id="promoter-details")
    company = promo_tab.find("label", text="Company Name").find_next_sibling("div").text.strip()
    address = promo_tab.find("label", text="Registered Office Address").find_next_sibling("div").text.strip()
    gst = promo_tab.find("label", text="GST No").find_next_sibling("div").text.strip()
    return {
        "Rera Regd. No": rera_no,
        "Project Name": proj_name,
        "Promoter Name": company,
        "Promoter Address": address,
        "GST No.": gst
    }

def main():
    st.title("Odisha RERA Project Scraper")
    num = st.slider("Number of projects to scrape", 1, 20, 6)
    if st.button("Scrape"):
        with st.spinner(f"Fetching first {num} projects…"):
            rows = fetch_project_rows(num)
            data = []
            for row in rows:
                link = row.find("a", text="View Details")["href"]
                data.append(parse_detail_page(link))
            df = pd.DataFrame(data)
        st.success("Done!")
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "projects.csv")

if __name__ == "__main__":
    main()

