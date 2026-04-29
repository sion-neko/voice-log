@echo off
chcp 65001 > nul
echo =====================================
echo AI Speech Summarization を起動しています...
echo =====================================

REM バッチファイルのディレクトリへ移動
cd /d "%~dp0"

REM バックエンド・フロントエンドの起動（Windows Terminal の新しいタブ）
echo Backend / Frontend サーバーを起動中...
wt new-tab --title "Backend" -- cmd /k "cd /d "%~dp0backend" && venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000" ; new-tab --title "Frontend" -- cmd /k "cd /d "%~dp0frontend" && npm run dev"

REM バックエンド起動待ち（疎通確認ポーリング）
echo バックエンドの起動を待機しています...
:wait_backend
curl -s http://localhost:8000/docs > nul 2>&1
if errorlevel 1 (
    timeout /t 2 > nul
    goto wait_backend
)
echo バックエンドの起動を確認しました。

REM ブラウザで開く（Viteのデフォルトポートは5173）
echo ブラウザを開いています...
start http://localhost:5173
