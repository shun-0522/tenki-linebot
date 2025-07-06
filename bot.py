from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone, timedelta

# .env 読み込み
load_dotenv()

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# デバッグ用：環境変数出力
print("アクセストークン:", LINE_CHANNEL_ACCESS_TOKEN)
print("チャネルシークレット:", LINE_CHANNEL_SECRET)
print("天気APIキー:", API_KEY)

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 東京の緯度・経度
LAT = 35.682839
LON = 139.759455

@app.route("/")
def index():
    return "LINE Bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print("★★ body 内容:", body, flush=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("署名エラーです", flush=True)
        return 'Invalid signature. Please check your channel access token/channel secret.', 400
    except Exception as e:
        print(f"その他の例外発生: {e}", flush=True)
        return 'Error', 500

    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip().replace(" ", "").lower()

    if "天気" in user_message:
        url = (
            f"https://api.openweathermap.org/data/2.5/onecall?"
            f"lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
        )

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            current_weather = current["weather"][0]["description"]
            current_temp = current["temp"]

            hourly_forecasts = data["hourly"][:5]
            hourly_texts = []
            for h in hourly_forecasts:
                dt = h["dt"]
                temp = h["temp"]
                weather_desc = h["weather"][0]["description"]
                dt_jst = datetime.fromtimestamp(dt, tz=timezone.utc) + timedelta(hours=9)
                time_str = dt_jst.strftime("%H:%M")
                hourly_texts.append(f"{time_str}: {weather_desc}, {temp}℃")

            hourly_info = "\n".join(hourly_texts)

            reply_text = f"【現在の天気】\n{current_weather}、{current_temp}℃\n\n【1時間ごとの予報】\n{hourly_info}"
        else:
            reply_text = "天気情報の取得に失敗しました。"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"あなたが送ったメッセージ: {user_message}")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)