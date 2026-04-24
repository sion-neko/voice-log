# AI Speech Summarization 🎙️✨

AIを活用した高精度な音声文字起こし、話者分離、および要約ツールです。  
会議や講義の音声をアップロードするだけで、誰が何を話したかを自動的に判別し、重要なポイントを整理して Notion へ保存します。

![UI Mockup](https://raw.githubusercontent.com/sion-neko/AI_SpeechSummarization/main/docs/ui_screenshot.png)
*※UIのイメージ画像です*

## ✨ 主な機能

- **🚀 高精度文字起こし**: `faster-whisper` を使用し、ローカル環境で高速かつ正確に音声をテキスト化します。
- **👥 自動話者分離 (Diarization)**: `pyannote.audio` を活用し、複数の話者を自動的に識別。かわいい動物アイコンで色分けして表示します。
- **📝 インテリジェント要約**: OpenAI GPT モデルを使用して、長い会話から「トピック」「要約」「重要なハイライト」を抽出します。
- **📓 Notion 連携**: 生成された要約とハイライトを、整理されたフォーマットで Notion のデータベースへ自動保存します。
- **🔄 インタラクティブ・ビューア**: 
    - 文字起こし全文と要約をタブで切り替え。
    - タイムスタンプをクリックして、その時点の音声を再生可能。
    - 各ステップ（文字起こし、要約、Notion出力）の進捗をリアルタイムで確認。
- **🛠️ エラーリカバリ**: 処理が途中で失敗しても、失敗したステップから再試行できるリトライ機能を搭載。

## 🏗️ システム構成

- **Frontend**: React, Vite, TypeScript, CSS Modules
- **Backend**: FastAPI (Python), faster-whisper, pyannote.audio
- **AI Models**: 
    - Transcription: Whisper
    - Diarization: Pyannote
    - Summarization: OpenAI API

## 🚀 セットアップ

### 1. 必要条件
- Python 3.10+
- Node.js & npm
- FFmpeg (パスが通っていること)
- OpenAI API Key
- Notion API Token & Database ID

### 2. 環境変数の設定
ルートディレクトリの `.env` ファイルに以下の情報を設定してください。

```env
OPENAI_API_KEY=your_openai_key
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
```

### 3. バックエンドの起動
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate / Mac: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### 4. フロントエンドの起動
```bash
cd frontend
npm install
npm run dev
```

## 🛠️ 開発者向け
各処理のステータスは `backend/output/{folder_id}/status.json` で管理されています。
文字起こし結果は `transcription.json`、要約結果は `summary.json` として各フォルダに保存されます。

---

Developed with ❤️ for efficient communication.
