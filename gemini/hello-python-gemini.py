import os
import sys
from google import genai
from google.genai import errors


def main():
    # 環境変数からAPIキーを取得
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "エラー: GEMINI_API_KEY 環境変数が設定されていません。",
            file=sys.stderr,
        )
        print("export GEMINI_API_KEY='your_api_key' を実行してください。", file=sys.stderr)
        sys.exit(1)

    # クライアントの初期化
    client = genai.Client(api_key=api_key)

    # 使用するモデル（標準的なテキストモデル）
    model_id = "gemini-3.5-flash"

    print(f"=== Gemini CUI アプリ (Model: {model_id}) ===")
    print("終了するには 'exit' または 'quit' と入力してください。\n")

    # チャットセッションの開始（会話履歴を維持するため）
    chat = client.chats.create(model=model_id)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("終了します。")
                break

            if not user_input.strip():
                continue

            print("Gemini: 思考中...", end="\r")

            # メッセージの送信とレスポンスの取得
            response = chat.send_message(user_input)

            # 行頭の「思考中...」をクリアして出力
            print(" " * 20, end="\r")
            print(f"Gemini: {response.text}")

        except errors.APIError as e:
            print(f"\nAPIエラーが発生しました: {e}")
        except KeyboardInterrupt:
            print("\n終了します。")
            break


if __name__ == "__main__":
    main()