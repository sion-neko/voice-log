# Speech to Text

ローカルLLM環境で音声を文字起こしするためのツールです。  
Ollama と Python を使用して動作します。


# 環境構築手順

## 1. Ollama のインストール

以下の公式サイトから Ollama をインストールしてください。

https://ollama.com/

インストール後、以下のコマンドで動作確認ができます。

```bash
ollama --version
```

Ollama のサーバーを起動します。

```bash
ollama serve
```

## 2. Python 環境の構築
仮想環境を作成します。

```bash
python -m venv venv
```

仮想環境を有効化します。

```bash
source venv/Scripts/activate
```

必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

## 3. ffmpeg のインストール
m4aをwavに変換するためのツールです。
以下からダウンロードし、パスを通してください。
https://github.com/BtbN/FFmpeg-Builds/releases

```bash
export PATH=$PATH:/d/ffmpeg/bin
```

m4aをwavに変換します。

```bash
ffmpeg -y -i input/lesson.m4a -ac 1 -ar 16000 -vn output.wav
```

## 4. プログラムの実行

以下のコマンドで音声の文字起こしAPIサーバーを起動できます。

```bash
uvicorn main:app --reload
```

## 5. フロントエンドの実行

以下のコマンドでフロントエンドを起動できます。

```bash
npm run dev
```


# 備考

* Ollama が起動していない場合、プログラムは動作しません
* 必要に応じて Ollama のモデルを事前に pull してください



