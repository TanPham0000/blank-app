import streamlit as st
import requests
from bs4 import BeautifulSoup
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()
NOTION_TOKEN = st.secrets["NOTION_TOKEN"] or os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = st.secrets["NOTION_DATABASE_ID"] or os.getenv("NOTION_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

def chunk_text(text, chunk_size=2000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

st.title("Vacature naar Notion")

urls_input = st.text_area(
    "Voer één of meerdere vacature-URL's in (één per regel):",
    height=150
)

if st.button("Scrape en stuur naar Notion") and urls_input.strip():
    urls = [line.strip() for line in urls_input.splitlines() if line.strip()]
    success_count = 0
    fail_urls = []

    for url in urls:
        try:
            res = requests.get(url)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            title_tag = soup.select_one("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Geen titel"

            wrapper = soup.select_one("#pagewrapper")
            targets = ["h2", "p", "li"]
            content_blocks = wrapper.select(",".join(targets)) if wrapper else []

            full_text = "\n\n".join(el.get_text(strip=True) for el in content_blocks)
            description = full_text[:2000]
            extra = full_text[2000:] if len(full_text) > 2000 else ""

            properties = {
                "Title": {"title": [{"text": {"content": title}}]},
                "Description": {"rich_text": [{"text": {"content": description}}]},
                "Date": {"date": {"start": datetime.now().isoformat()}}
            }

            if extra:
                extra_chunks = chunk_text(extra, 2000)
                properties["Extra"] = {
                    "rich_text": [{"text": {"content": chunk}} for chunk in extra_chunks]
                }

            notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=properties)
            success_count += 1
        except Exception as e:
            fail_urls.append((url, str(e)))

    st.success(f"✅ {success_count} vacatures succesvol naar Notion gestuurd.")
    if fail_urls:
        st.error("❌ De volgende URL's konden niet worden verwerkt:")
        for fail_url, err_msg in fail_urls:
            st.write(f"- {fail_url}: {err_msg}")