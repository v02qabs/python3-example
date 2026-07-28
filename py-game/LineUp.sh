#!/bin/bash

# --- 引数のチェック ---
if [ "$#" -ne 3 ]; then
    echo "使用方法: $0 <アップロードしたいファイル名.txt> <プロンプト> <結果出力先ファイル.txt>"
    exit 1
fi

FILE_PATH="$1"
PROMPT="$2"
OUTPUT_FILE="$3"

# --- 設定 ---
API_KEY="${GEMINI_API_KEY}"
if [ -z "$API_KEY" ]; then
    echo "エラー:  환경変数 GEMINI_API_KEY が設定されていません。"
    exit 1
fi

# 使用するモデル（例: gemini-2.5-flash）
MODEL="gemini-2.5-flash"

# --- 1. ファイルのアップロード (Files API) ---
echo "ファイルをアップロード中..." >&2

# ファイルのサイズとMIMEタイプを取得
FILE_SIZE=$(wc -c < "$FILE_PATH")
MIME_TYPE="text/plain" # 必要に応じて変更

# Step 1: アップロードセッションの開始とファイルアップロード
# (Gemini APIのFiles APIを使用)
UPLOAD_RESPONSE=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/upload/v1beta/files?key=${API_KEY}" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${FILE_SIZE}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{\"file\": {\"display_name\": \"$(basename "$FILE_PATH")\"}}")

# アップロード用URLの取得
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | grep -i "x-goog-upload-url" | tr -d '\r' | awk '{print $2}')

if [ -z "$UPLOAD_URL" ]; then
    echo "エラー: アップロードURLの取得に失敗しました。" >&2
    echo "$UPLOAD_RESPONSE" >&2
    exit 1
fi

# Step 2: 実際のデータ送信
FILE_URI_RESPONSE=$(curl -s -X POST "$UPLOAD_URL" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  -H "Content-Length: ${FILE_SIZE}" \
  -H "Content-Type: ${MIME_TYPE}" \
  --data-binary "@${FILE_PATH}")

# アップロードされたファイルのURIを取得
FILE_URI=$(echo "$FILE_URI_RESPONSE" | grep -o '"uri": *"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$FILE_URI" ]; then
    echo "エラー: ファイルのURI取得に失敗しました。" >&2
    echo "$FILE_URI_RESPONSE" >&2
    exit 1
fi

echo "アップロード完了: $FILE_URI" >&2

# --- 2. プロンプトの送信と結果の取得 (Generate Content API) ---
echo "Geminiに問い合わせ中..." >&2

# JSONペイロードの作成（jqコマンドを使うと安全ですが、ここではヒードキュメントで構築）
PAYLOAD=$(cat <<EOF
{
  "contents": [
    {
      "parts": [
        {
          "file_data": {
            "mime_type": "${MIME_TYPE}",
            "file_uri": "${FILE_URI}"
          }
        },
        {
          "text": "${PROMPT}"
        }
      ]
    }
  ]
}
EOF
)

# APIリクエストの実行
API_RESPONSE=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# --- 3. 結果の抽出と出力 ---
# jqコマンドを使用してレスポンスからテキストを抽出
if command -v jq &> /dev/null; then
    RESULT=$(echo "$API_RESPONSE" | jq -r '.candidates[0].content.parts[0].text // empty')
else
    # jqがない場合は簡易的にgrep/sedで抽出を試みる（非推奨だがフォールバック用）
    echo "警告: jqコマンドが見つからないため、レスポンスの解析が不安定になります。" >&2
    RESULT="$API_RESPONSE"
fi

if [ -z "$RESULT" ]; then
    echo "エラー: APIからの応答の取得に失敗しました。" >&2
    echo "$API_RESPONSE" >&2
    exit 1
fi

# 結果を指定ファイルに出力
echo "$RESULT" > "$OUTPUT_FILE"
echo "完了しました。結果を ${OUTPUT_FILE} に保存しました。" >&2
