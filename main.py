from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Разрешаем доступ (для простоты)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def search_wbcon(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    # запрос поиска
    response = requests.get("https://wbcon.ru/", params={"s": query}, headers=headers, timeout=20)
    if response.status_code != 200:
        return {"error": f"Failed to fetch search page, status={response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")

    # ищем первую ссылку на статью (WordPress обычно так размечает)
    link = None
    title = None
    candidates = soup.select("h2 a, h3 a, .entry-title a, .post-title a")

    for a in candidates:
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href.startswith("https://wbcon.ru/") and text:
            link = href
            title = text
            break

    if not link:
        snippet = soup.get_text("\n", strip=True)[:600]
        return {"error": "Nothing found", "debug_snippet": snippet}

    # тянем статью
    article_response = requests.get(link, headers=headers, timeout=20)
    if article_response.status_code != 200:
        return {"error": f"Failed to fetch article, status={article_response.status_code}", "url": link}

    article_soup = BeautifulSoup(article_response.text, "html.parser")
    content_div = article_soup.select_one("div.entry-content, article .entry-content, .post-content, .content")

    content_text = content_div.get_text(separator="\n", strip=True) if content_div else "No content extracted"

    return {
        "title": title,
        "url": link,
        "content": content_text[:7000]
    }
    
@app.get("/search")
def search(q: str = Query(..., description="Search query")):
    return search_wbcon(q)


@app.get("/health")
def health():
    return {"status": "ok"}