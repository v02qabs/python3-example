#!/bin/bash

# --- 設定 ---
# 環境変数 GEMINI_API_KEY が設定されている前提ですが、
# 直接記述する場合は下の "" にキーを入れてください。
API_KEY="${GEMINI_API_KEY}"

# 使用するモデル（必要に応じて変更してください）
MODEL="gemini-1.5-flash"

# --- 引数のチェック ---
if [ "$#" -lt 3 ]; then
    echo "使用方法: $0 <プロンプト文> <アップロードファイル> <savefile.txt>"
    echo "例: $0 \"このファイルを要約して\" sample.pdf result.txt"
    exit 1
fi

PROMPT="$1"
FILE_PATH="$2"
SAVE_FILE="$3"

if [ -z "$API_KEY" ]; then
    echo "エラー: GEMINI_API_KEY 環境変数が設定されていません。"
    echo "export GEMINI_API_KEY='あなたのAPIキー' を実行してから再度お試しください。"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "エラー: ファイル '$FILE_PATH' が見つかりません。"
    exit 1
fi

echo "1. ファイルをアップロード中... ($FILE_PATH)"

# ファイルのサイズとMIMEタイプの取得
FILE_SIZE=$(wc -c < "$FILE_PATH" | tr -d ' ')
MIME_TYPE=$(file --mime-type -b "$FILE_PATH")

echo "MIMEタイプ: $MIME_TYPE"

# Step 1: Resumable Uploadの開始 (アップロードURLの取得)
UPLOAD_URL_RESPONSE=$(curl -s -D - \
  "https://generativelanguage.googleapis.com/upload/v1beta/files?key=${API_KEY}" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${FILE_SIZE}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{\"file\": {\"display_name\": \"$(basename "$FILE_PATH")\"}}")

#レスポンスヘッダーからアップロード用URL(X-Goog-Upload-URL)を抽出
UPLOAD_URL=$(echo "$UPLOAD_URL_RESPONSE" | grep -i "x-goog-upload-url:" | tr -d '\r' | awk '{print $2}')

if [ -z "$UPLOAD_URL" ]; then
    echo "エラー: アップロードURLの取得に失敗しました。"
    echo "$UPLOAD_URL_RESPONSE"
    exit 1
fi

# Step 2: 実際のファイルデータの送信
UPLOAD_RESULT=$(curl -s \
  "$UPLOAD_URL" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "Content-Length: ${FILE_SIZE}" \
  -H "Content-Type: ${MIME_TYPE}" \
  --data-binary "@${FILE_PATH}")

# アップロードされたファイルのURIと名前を取得
FILE_URI=$(echo "$UPLOAD_RESULT" | grep -o '"uri": *"[^"]*"' | head -1 | cut -d'"' -f4)
RESOURCE_NAME=$(echo "$UPLOAD_RESULT" | grep -o '"name": *"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$FILE_URI" ]; then
    echo "エラー: ファイルのアップロードに失敗しました。"
    echo "$UPLOAD_RESULT"
    exit 1
fi

echo "アップロード成功! URI: $FILE_URI"
echo "2. プロンプトを送信して生成中..."

# Step 3: GeminiにファイルURIとプロンプトを送信
API_RESPONSE=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{
    \"contents\": [
      {
        \"parts\": [
          {
            \"file_data\": {
              \"file_uri\": \"${FILE_URI}\",
              \"mime_type\": \"${MIME_TYPE}\"
            }
          },
          {
            \"text\": \"${PROMPT}\"
          }
        ]
      }
    ]
  }")

# 応答からテキスト部分を抽出してファイルに保存
# (簡易的にjqコマンドを使うのがベストですが、jqがない環境を考慮してPythonまたはgrep/sedで処理するか、jq推奨とします)
if command -v jq &> /dev/null; then
    echo "$API_RESPONSE" | jq -r '.candidates[0].content.parts[0].text' > "$SAVE_FILE"
else
    # jqがない場合はレスポンスをそのまま保存（またはPythonでパース）
    echo "$API_RESPONSE" | python3 -c "import sys, json; res=json.load(sys.stdin); print(res['candidates'][0]['content']['parts'][0]['text'])" > "$SAVE_FILE"
fi

echo "完了しました。結果は '$SAVE_FILE' に保存されました。"

# オプション: アップロードしたファイルをAPI側からも削除したい場合は以下のコメントアウトを外す
# curl -s -X DELETE "https://generativelanguage.googleapis.com/v1beta/${RESOURCE_NAME}?key=${API_KEY}" > /dev/null