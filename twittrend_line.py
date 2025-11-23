def fetch_trends_top50():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    resp = requests.get(TWITTREND_URL, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 「日本のトレンド」
    japan_header = soup.find(
        ["h4", "h3"],
        string=lambda x: x and "日本のトレンド" in x
    )
    if not japan_header:
        raise RuntimeError("日本のトレンドセクションが見つかりませんでした")

    # 「現在」
    current_header = japan_header.find_next(
        ["h2", "h3"],
        string=lambda x: x and "現在" in x
    )
    if not current_header:
        raise RuntimeError("「現在」セクションが見つかりませんでした")

    ul = current_header.find_next("ul")
    if not ul:
        raise RuntimeError("トレンド一覧の <ul> が見つかりませんでした")

    li_tags = ul.find_all("li")
    if not li_tags:
        raise RuntimeError("トレンドの <li> が見つかりませんでした")

    trends = []
    for li in li_tags[:50]:
        text = li.get_text(strip=True)
        text = re.sub(r"^\d+\.\s*", "", text)
        text = re.sub(r"\s+", " ", text)
        trends.append(text)

    return trends
