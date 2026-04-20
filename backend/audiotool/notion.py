import requests
import logging
import os

logger = logging.getLogger(__name__)

url = "https://api.notion.com/v1/pages"

VOICE_PAGE_ID = os.environ.get("VOICE_PAGE_ID")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")


def create_notion_page(title: str, content: str):
    # Notionの仕様で、1つのリッチテキストコンテンツは最大2000文字の制限があります
    # 制限を回避するため、2000文字ごとに分割して複数の段落ブロックとして作成します
    chunk_size = 2000
    children_blocks = []

    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        children_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "text": {
                            "content": chunk
                        }
                    }
                ]
            }
        })

    payload = {
        "parent": {
            "page_id": VOICE_PAGE_ID
        },
        "properties": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        },
        "children": children_blocks
    }
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {e}")


def format_and_save_summary(title: str, summary_result: dict):
    """
    要約結果(dict)を受け取り、いい感じのテキストにフォーマットしてNotionに保存する
    """
    formatted_text = ""

    topics = summary_result.get("topics", [])
    if not topics:
        formatted_text = "要約データがありません。"

    for i, topic in enumerate(topics, 1):
        t_title = topic.get("title", "無題")
        t_summary = topic.get("summary", "")

        formatted_text += f"■ {i}. {t_title}\n"
        formatted_text += f"{t_summary}\n\n"

        highlights = topic.get("highlights", [])
        if highlights:
            formatted_text += "【重要な発言】\n"
            for h in highlights:
                start = h.get("start", 0.0)
                try:
                    start_val = float(start)
                except (ValueError, TypeError):
                    start_val = 0.0

                mm, ss = divmod(int(start_val), 60)
                hh, mm = divmod(mm, 60)
                time_str = f"[{hh:02d}:{mm:02d}:{ss:02d}]" if hh > 0 else f"[{mm:02d}:{ss:02d}]"

                speaker = h.get("speaker", "Unknown")
                text = h.get("text", "")
                reason = h.get("reason", "")

                if reason:
                    formatted_text += f"{time_str} {speaker}: 「{text}」 (理由: {reason})\n"
                else:
                    formatted_text += f"{time_str} {speaker}: 「{text}」\n"
            formatted_text += "\n"
        formatted_text += "----------------------------------------\n\n"

    # 保存処理
    create_notion_page(title, formatted_text.strip())


def format_and_save_transcription(title: str, diarization_result: dict):
    """
    文字起こし結果(dict)を受け取り、いい感じのテキストにフォーマットしてNotionに保存する
    """
    formatted_text = ""
    segments = diarization_result.get("segments", [])

    if not segments:
        formatted_text = "文字起こしデータがありません。"

    for segment in segments:
        start = segment.get("start", 0.0)
        try:
            start_val = float(start)
        except (ValueError, TypeError):
            start_val = 0.0

        mm, ss = divmod(int(start_val), 60)
        hh, mm = divmod(mm, 60)
        time_str = f"[{hh:02d}:{mm:02d}:{ss:02d}]" if hh > 0 else f"[{mm:02d}:{ss:02d}]"

        speaker = segment.get("speaker") or "Unknown"
        text = segment.get("text", "").strip()

        formatted_text += f"{time_str} {speaker}: {text}\n"

    # 保存処理
    create_notion_page(title, formatted_text.strip())
