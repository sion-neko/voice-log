import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4"


def _build_transcript(segments: list[dict]) -> str:
    """セグメントリストをタイムスタンプ付きのテキストに変換する"""
    lines = []
    for seg in segments:
        start = seg.get("start", 0)
        speaker = seg.get("speaker", "話者")
        text = seg.get("text", "")
        lines.append(f"[{start:.1f}s] {speaker}: {text}")
    return "\n".join(lines)


def _build_prompt(transcript: str) -> str:
    return f"""以下は音声の文字起こし結果です。タイムスタンプと話者ラベルが付いています。

{transcript}

上記の内容を分析し、話題（章）ごとに分類してください。以下のJSON形式のみで回答してください。余分な説明は不要です。

{{
  "topics": [
    {{
      "title": "話題のタイトル（短く簡潔に）",
      "summary": "この話題の要約（2〜3文程度）",
      "highlights": [
        {{
          "start": <開始時間(秒, 数値)>,
          "speaker": "<話者ラベル>",
          "text": "重要な発言（文字起こしの原文をそのまま抜き出す）",
          "reason": "重要な理由（10〜20文字程度）"
        }}
      ]
    }}
  ]
}}

ルール:
- topics は内容の流れに沿って2〜5個に分ける
- 各 topic の title は短く簡潔な日本語で書く
- 各 topic の summary は日本語で簡潔に書く
- 各 topic の highlights は重要度が高い発言を1〜3個選ぶ
- highlights の text は必ず文字起こしの原文から一字一句そのまま抜き出す（要約・改変禁止）
- highlights の start はその発言が始まる秒数（数値）を記載する
- 回答はJSONのみ。マークダウンのコードブロック（```）は不要"""


def _extract_json(text: str) -> dict:
    """LLMの返答からJSONを抽出してパースする"""
    # コードブロックを除去
    text = re.sub(r"```(?:json)?", "", text).strip()

    # JSONオブジェクトを探す
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise ValueError(f"JSON not found in response: {text[:200]}")


def summarize(segments: list[dict]) -> dict:
    """
    セグメントリストを受け取り、話題ごとの要約と重要箇所を返す。

    Returns:
        {
            "topics": [
                {
                    "title": str,
                    "summary": str,
                    "highlights": [
                        {
                            "start": float,
                            "speaker": str,
                            "text": str,      # 原文抜き出し
                            "reason": str
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """

    transcript = _build_transcript(segments)
    prompt = _build_prompt(transcript)

    print("Summarizing with Ollama...")
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        return {"topics": [{"title": "エラー", "summary": "要約に失敗しました。Ollamaへの接続を確認してください。", "highlights": []}]}

    raw = res.json().get("response", "")
    print(f"Raw response: {raw[:300]}")

    try:
        result = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"JSON parse error: {e}")
        return {"topics": [{"title": "要約結果", "summary": raw, "highlights": []}]}

    # highlights の start を float に強制変換
    for topic in result.get("topics", []):
        for h in topic.get("highlights", []):
            try:
                h["start"] = float(h.get("start", 0))
            except (TypeError, ValueError):
                h["start"] = 0.0

    return result


if __name__ == "__main__":
    # テスト用
    test_segments = [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00",
            "text": "今日の会議を始めます。議題はQ3の予算計画です。"},
        {"start": 5.0, "end": 12.0, "speaker": "SPEAKER_01",
            "text": "Q3の目標を20%引き上げることを提案します。理由は市場の回復が予想より早いからです。"},
        {"start": 12.0, "end": 18.0, "speaker": "SPEAKER_00",
            "text": "了解しました。では各部署のコスト削減案も併せて検討お願いします。"},
        {"start": 18.0, "end": 25.0, "speaker": "SPEAKER_01",
            "text": "はい。来週までに資料を準備します。"},
        {"start": 25.0, "end": 30.0, "speaker": "SPEAKER_00",
            "text": "では、来週の月曜日にまた集まりましょう。以上です。"},
    ]
    result = summarize(test_segments)
    print(json.dumps(result, ensure_ascii=False, indent=2))
