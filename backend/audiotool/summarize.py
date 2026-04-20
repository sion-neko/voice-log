import json
import logging
import re
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

SUMMARIZE_MODEL = os.environ.get("SUMMARIZE_MODEL")
SUMMARIZE_API_KEY = os.environ.get("SUMMARIZE_API_KEY")
SUMMARIZE_BASE_URL = os.environ.get("SUMMARIZE_BASE_URL")


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
    return f"""# やること
レッスン音声の文字起こしを元に、振り返り用に章分けと要約をしてください。
レッスン音声の文字起こしの性能はあまり高くないので内容は適宜推測して読み替えてください。
レッスン音声の文字起こしにはタイムスタンプと話者ラベルが付いています。

# レッスン音声の文字起こし
{transcript}

# 出力形式
レッスン音声の文字起こしを分析し、振り返り用に章分けと要約をしてください。
以下のJSON形式のみで回答してください。余分な説明は不要です。

{{
  "topics": [
    {{
      "title": "章のタイトル（短く簡潔に）",
      "summary": "この章の要約（2〜3文程度）",
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

    logger.info(f"Summarizing with model={SUMMARIZE_MODEL}...")
    try:
        kwargs = {"api_key": SUMMARIZE_API_KEY, "base_url": SUMMARIZE_BASE_URL}
        client = OpenAI(**kwargs)
        response = client.responses.create(
            model=SUMMARIZE_MODEL,
            input=prompt,
            temperature=0.3,
            timeout=120,
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return {"topics": [{"title": "エラー", "summary": f"要約に失敗しました: {e}", "highlights": []}]}

    raw = response.output_text or ""
    logger.debug(f"Raw response: {raw[:300]}")

    try:
        result = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"JSON parse error: {e}")
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
