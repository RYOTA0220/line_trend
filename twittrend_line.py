def send_line_message(text):
    import os
    import requests

    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")

    if not channel_access_token:
        raise RuntimeError("環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
    if not group_id:
        raise RuntimeError("環境変数 LINE_GROUP_ID が設定されていません")

    # デバッグ用に長さだけ出す（中身は出さない）
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

    # ここでレスポンスを丸見えにする
    print("LINE API status:", resp.status_code)
    print("LINE API body:", resp.text[:500])

    # 200 以外ならエラーにする
    resp.raise_for_status()
