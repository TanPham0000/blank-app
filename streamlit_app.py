import streamlit as st
import requests
from bs4 import BeautifulSoup
from notion_client import Client
from dotenv import load_dotenv
import os


# Laad .env lokaal (of werkt met st.secrets op Streamlit Cloud)
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or st.secrets["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or st.secrets["NOTION_DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

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
        properties["Extra"] = {"rich_text": [{"text": {"content": extra}}]}

    notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=properties)
    st.success("✅ Vacature succesvol naar Notion gestuurd.")
