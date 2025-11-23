import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

TWITTREND_URL = "https://twittrend.jp/"


def fetch_trends_top50():
    resp = requests.get(TWITTREND_URL, timeout=10)
    resp.raise_for_status()
    # 念のためエンコーディング指定
    resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # 「日本のトレンド」→「現在」のブロックを探す
    # （HTML側では h4,h2,h3 などで構成されている）
    japan_header = soup.find(
        ["h4", "h3"],
        string=lambda x: x and "日本のトレンド" in x
    )
    if not japan_header:
        raise RuntimeError("日本のトレンドセクションが見つかりませんでした")

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
        # 先頭の「1. 」みたいな順位を削る
        text = re.sub(r"^\d+\.\s*", "", text)
        # 変な改行を潰す
        text = re.sub(r"\s+", " ", text)
        trends.append(text)

    return trends


def build_message(trends):
    # GitHub Actions は UTC なので JST に変換
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

    # LINEのテキスト上限（5000文字）対策（ほぼ大丈夫だと思うけど一応）
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
    if resp.status_code != 200:
        raise RuntimeError(
            f"LINE送信失敗: status={resp.status_code}, body={resp.text}"
        )


def main():
    trends = fetch_trends_top50()
    message = build_message(trends)
    send_line_message(message)


if __name__ == "__main__":
    main()
