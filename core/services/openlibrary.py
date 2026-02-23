import requests


def search_books(query: str, limit: int = 10) -> list[dict]:
    url = "https://openlibrary.org/search.json"
    r = requests.get(url, params={"q": query, "limit": limit}, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = []
    for doc in data.get("docs", []):
        title = doc.get("title") or "Untitled"
        year = doc.get("first_publish_year")
        authors = doc.get("author_name", [])[:3]
        olid = None
        if doc.get("edition_key"):
            olid = doc["edition_key"][0]  

        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else ""

        results.append(
            {
                "title": title,
                "year": year,
                "authors": authors,
                "source": "openlibrary",
                "source_id": olid or "",
                "cover_url": cover_url,
            }
        )

    return results