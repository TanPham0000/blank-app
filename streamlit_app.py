import streamlit as st
import requests
from bs4 import BeautifulSoup
from notion_client import Client
from dotenv import load_dotenv
import os

load_dotenv()
NOTION_TOKEN = st.secrets["NOTION_TOKEN"] or os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = st.secrets["NOTION_DATABASE_ID"] or os.getenv("NOTION_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

def chunk_text(text, chunk_size=2000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

st.title("Vacature naar Notion")
url = st.text_input("Voer een vacature-URL in:")

if st.button("Scrape en stuur naar Notion") and url:
    res = requests.get(url)
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
    }

    if extra:
        extra_chunks = chunk_text(extra, 2000)
        # Create a list of rich_text blocks for the 'Extra' property
        properties["Extra"] = {
            "rich_text": [{"text": {"content": chunk}} for chunk in extra_chunks]
        }

    notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=properties)
    st.success("✅ Vacature succesvol naar Notion gestuurd.")