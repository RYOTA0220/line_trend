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

    # ページ内の <ul> を全部見て、一番 li の数が多いものを
    # 「日本のトレンド 現在」のリストとみなす
    best_ul = None
    best_count = 0

    for ul in soup.find_all("ul"):
        li_tags = ul.find_all("li")
        count = len(li_tags)
        if count > best_count:
            best_count = count
            best_ul = ul

    # 20個も li がない場合は、構造が大きく変わっていると判断してエラー
    if not best_ul or best_count < 20:
        raise RuntimeError("トレンド一覧の <ul> が見つかりませんでした（li が少なすぎます）")

    li_tags = best_ul.find_all("li")

    trends = []
    # 最大50位まで。49位しかなくてもOK、それ以下は無視
    for li in li_tags[:50]:
        text = li.get_text(strip=True)
        # 先頭の「1. 」みたいな番号を消す
        text = re.sub(r"^\d+\.\s*", "", text)
        # 余計な改行やスペースをまとめる
        text = re.sub(r"\s+", " ", text)
        trends.append(text)

    return trends
