import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

TWITTREND_URL = "https://twittrend.jp/"


def fetch_trends_top50():
    """Twittrend から日本の現在トレンドを最大50位まで取得する。"""
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

    # 20個も li がない場合は構造が変わっていると判断
    if not best_ul or best_count < 20:
        raise RuntimeError("トレンド一覧の <ul> が見つかりませんでした（li が少なすぎます）")

    li_tags = best_ul.find_all("li")

    trends = []
    # 最大50位まで。49位しかなくてもOK
    for li in li_tags[:50]:
        text = li.get_text(strip=True)
        # 先頭の「1. 」のような番号を除去
        text = re.sub(r"^\d+\.\s*", "", text)
        # 余計な空白を1つに
        text = re.sub(r"\s+", " ", text)
        trends.append(text)

    return trends


def build_message(trends):
    """トレンドのリストからLINEに送るテキストを組み立てる（吹き出し1個分）。"""
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

    # LINEの上限対策（余裕をもって絞る）
    if len(message) > 4800:
        message = message[:4800] + "\n…（一部省略）"

    return message


def send_line_message(text):
    """LINEにテキストを1メッセージ（吹き出し1個）で送信する。"""
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
        ],  # ← 要素1つなので吹き出し1個
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)

    # レスポンス確認
    print("LINE API status:", resp.status_code)
    print("LINE API body:", resp.text[:500])

    resp.raise_for_status()


def main():
    # 1〜50位（たまに49位）まで全部取得
    trends = fetch_trends_top50()
    print("DEBUG: trends count =", len(trends))

    # 全件を1つのメッセージにまとめて送信
    message = build_message(trends)
    send_line_message(message)


if __name__ == "__main__":
    main()
