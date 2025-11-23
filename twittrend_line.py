import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

TWITTREND_URL = "https://twittrend.jp/"


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


def build_message(trends):
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(tz=jst)
    header = (
        "📈 Xトレンド（日本 / 現在）\n"
        f"取得時刻: {now_jst.strftime('%Y-%m-%d %H:%M')}（JST）\n"
        "------------------------------"
    )

    lines = []
    for i, t in enumerate(trends, start=1):
        lines.append(f"{i}. {t}")

    body = "\n".join(lines)
    message = f"{header}\n{body}"

    if len(message) > 4800:
        message = message[:4800] + "\n…（一部省略）"

    return message


def send_line_message(text):
    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")

    if not channel_access_token:
        raise RuntimeError("環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
    if not group_id:
        raise RuntimeError("環境変数 LINE_GROUP_ID が設定されていません")

    # デバッグ出力
    print("DEBUG: token length =", len(channel_access_token))
    print("DEBUG: group_id =", group_id)

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": group_id,
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)

    # レスポンスを確認
    print("LINE API status:", resp.status_code)
    print("LINE API body:", resp.text[:500])

    resp.raise_for_status()


def main():
    trends = fetch_trends_top50()
    message = build_message(trends)
    send_line_message(message)


if __name__ == "__main__":
    main()
