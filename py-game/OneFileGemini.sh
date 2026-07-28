#!/bin/bash
set -e

# 引数チェック
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <アップロードするファイル.py> <log.txt>"
    exit 1
fi

INPUT_FILE="$1"
LOG_FILE="$2"

# ログファイルの保存先ディレクトリが存在しない場合は作成
mkdir -p "$(dirname "$LOG_FILE")"

if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY environment variable is not set." >&2
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found." >&2
    exit 1
fi

echo "1. ファイルをアップロード中: $INPUT_FILE ..."

FILE_SIZE=$(wc -c < "$INPUT_FILE" | tr -d ' ')
MIME_TYPE="text/x-python"

# Resumable Upload の開始
UPLOAD_URL="https://generativelanguage.googleapis.com/upload/v1beta/files?key=${GEMINI_API_KEY}"

SESSION_URI=$(curl -s -D - -X POST "$UPLOAD_URL" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Header-Content-Length: ${FILE_SIZE}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{\"file\": {\"display_name\": \"$(basename "$INPUT_FILE")\"}}" | grep -i "x-goog-upload-url:" | tr -d '\r' | awk '{print $2}')

if [ -z "$SESSION_URI" ]; then
    echo "Error: Failed to get upload session URI." >&2
    exit 1
fi

# ファイルデータのアップロード
FILE_URI=$(curl -s -X POST "$SESSION_URI" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "Content-Length: ${FILE_SIZE}" \
  --data-binary "@${INPUT_FILE}" | jq -r '.file.uri')

echo "アップロード完了: $FILE_URI"
echo "2. Gemini に解析を依頼中..."

# jq を使って安全に JSON ペイロードを生成（特殊文字・改行を自動エスケープ）
PAYLOAD=$(jq -n \
  --arg mime "$MIME_TYPE" \
  --arg uri "$FILE_URI" \
  '{
    "contents": [{
      "parts": [
        {"text": "以下のPythonコードの内容を解析し、改善点や説明を出力してください。"},
        {"file_data": {"mime_type": $mime, "file_uri": $uri}}
      ]
    }]
  }')

# リクエスト送信
RESPONSE=$(curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# レスポンス全体をログに保存
echo "$RESPONSE" > "$LOG_FILE"

# 結果を表示
if echo "$RESPONSE" | grep -q '"error"'; then
    echo "APIエラーが発生しました:"
    echo "$RESPONSE" | jq .
else
    echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text // "（応答本文を取得できませんでした）"'
fi