@echo off
chcp 65001 > nul
echo =====================================
echo こえログ を起動しています...
echo =====================================

REM バッチファイルのディレクトリへ移動
cd /d "%~dp0."

REM ---- フロントエンド: 初回セットアップ ----
if not exist "frontend\node_modules" (
    echo [Setup] node_modules が見つかりません。npm install を実行しています...
    cd frontend
    npm install
    if errorlevel 1 (
        echo [Error] npm install に失敗しました。Node.js がインストールされているか確認してください。
        cd /d "%~dp0."
        pause
        exit /b 1
    )
    cd /d "%~dp0."
    echo [Setup] フロントエンドのセットアップが完了しました。
)

REM ---- サーバー起動 ----
echo Backend / Frontend サーバーを起動中...
wt new-tab --title "Backend" -- cmd /k "cd /d "%~dp0." && wsl docker compose up --build" ; new-tab --title "Frontend" -- cmd /k "cd /d "%~dp0frontend" && npm run dev"

REM バックエンド起動待ち（疎通確認ポーリング、最大5分）
echo バックエンドの起動を待機しています（Docker ビルドがある場合は数分かかります）...
set RETRY=0
:wait_backend
curl -s http://localhost:8000/docs > nul 2>&1
if not errorlevel 1 goto backend_ready
set /a RETRY+=1
if %RETRY% geq 150 (
    echo [Error] バックエンドが5分以内に起動しませんでした。Backend タブのログを確認してください。
    pause
    exit /b 1
)
timeout /t 2 > nul
goto wait_backend
:backend_ready
echo バックエンドの起動を確認しました。

REM ブラウザで開く（Viteのデフォルトポートは5173）
echo ブラウザを開いています...
start http://localhost:5173
pause
