#!/bin/bash
set -e

# 引数のチェック（3つまたは4つに対応）
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
    echo "使用方法（ファイル1つの場合）: $0 <ファイル1> <プロンプト> <出力ファイル.txt>"
    echo "使用方法（ファイル2つの場合）: $0 <ファイル1> <ファイル2> <プロンプト> <出力ファイル.txt>"
    exit 1
fi

if [ "$#" -eq 3 ]; then
    FILE1="$1"
    FILE2=""
    PROMPT="$2"
    OUTPUT_FILE="$3"
else
    FILE1="$1"
    FILE2="$2"
    PROMPT="$3"
    OUTPUT_FILE="$4"
fi

# APIキーの確認
if [ -z "$GEMINI_API_KEY" ]; then
    echo "エラー: 環境変数 GEMINI_API_KEY が設定されていません。"
    echo "実行前に 'export GEMINI_API_KEY=\"your_api_key\"' を実行してください。"
    exit 1
fi

# モデルの指定 (最新モデル名を設定)
MODEL="gemini-3.6-flash"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

log "=== 処理開始 ==="

# ファイルアップロード用の関数
upload_file() {
    local filepath="$1"
    
    if [ ! -f "$filepath" ]; then
        echo "エラー: ファイルが存在しません: $filepath" >&2
        exit 1
    fi

    local filename=$(basename "$filepath")
    local filesize=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null)
    local mime_type=$(file --mime-type -b "$filepath")

    log "アップロード中: $filename ($mime_type)..."

    # 1. アップロードセッションの開始
    local meta_json
    meta_json=$(jq -n --arg name "$filename" '{"file": {"display_name": $name}}')

    local headers
    headers=$(curl -s -i -X POST \
        "https://generativelanguage.googleapis.com/upload/v1beta/files?key=$GEMINI_API_KEY" \
        -H "X-Goog-Upload-Protocol: resumable" \
        -H "X-Goog-Upload-Command: start" \
        -H "X-Goog-Upload-Header-Content-Length: $filesize" \
        -H "X-Goog-Upload-Header-Content-Type: $mime_type" \
        -H "Content-Type: application/json" \
        -d "$meta_json")

    # ヘッダーから upload URL を抽出
    local upload_url
    upload_url=$(echo "$headers" | grep -i "^x-goog-upload-url:" | tr -d '\r\n' | sed -E 's/^[xX]-[gG][oO][oO][gG][lL][eE]-[uU][pP][lL][oO][aA][dD]-[uU][rR][lL]:\s*//i' | awk '{print $1}')

    if [ -z "$upload_url" ]; then
        echo "エラー: アップロードURLの取得に失敗しました: $filename" >&2
        echo "$headers" | head -n 20 >&2
        exit 1
    fi

    # 2. ファイルデータの送信
    local response
    response=$(curl -sS -X POST "$upload_url" \
        -H "X-Goog-Upload-Protocol: resumable" \
        -H "X-Goog-Upload-Command: upload, finalize" \
        -H "Content-Length: $filesize" \
        -H "Content-Type: $mime_type" \
        --data-binary "@$filepath")

    local file_uri
    file_uri=$(echo "$response" | jq -r '.file.uri // empty')
    
    if [ -z "$file_uri" ]; then
        echo "エラー: ファイルURIの取得に失敗しました: $filename" >&2
        echo "レスポンス: $response" >&2
        exit 1
    fi

    echo "$file_uri"
}

# ファイル1のアップロード
URI1=$(upload_file "$FILE1")

# ファイル2があればアップロード
URI2=""
if [ -n "$FILE2" ]; then
    URI2=$(upload_file "$FILE2")
fi

log "Gemini APIにリクエストを送信中（モデル: ${MODEL}）..."

# parts 配列の構築
PARTS_JSON=$(jq -n --arg p "$PROMPT" --arg u1 "$URI1" '[{text: $p}, {file_data: {file_uri: $u1}}]')

if [ -n "$URI2" ]; then
    PARTS_JSON=$(echo "$PARTS_JSON" | jq --arg u2 "$URI2" '. + [{file_data: {file_uri: $u2}}]')
fi

PAYLOAD=$(jq -n --argjson parts "$PARTS_JSON" '{contents: [{parts: $parts}]}')

# Gemini API の呼び出し
RESPONSE=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD")

# レスポンスからテキスト抽出
RESULT_TEXT=$(echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text // empty')

if [ -z "$RESULT_TEXT" ]; then
    log "エラー: Geminiからの応答取得に失敗しました。"
    echo "--- APIレスポンス（デバッグ用） ---" >&2
    echo "$RESPONSE" | jq . >&2 || echo "$RESPONSE" >&2
    exit 1
fi

echo "$RESULT_TEXT" | tee "$OUTPUT_FILE"
log "完了しました。結果は '$OUTPUT_FILE' に保存されました。"