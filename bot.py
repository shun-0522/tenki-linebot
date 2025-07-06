import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ← ここに書く
API_KEY = os.environ.get("OPENWEATHER_API_KEY")
LAT = "35.6895"   # 東京の例
LON = "139.6917"

print("取得したAPI_KEY:", API_KEY)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip().replace(" ", "").lower()

    if "天気" in user_message:
        url = (
            f"https://api.openweathermap.org/data/2.5/onecall?"
            f"lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
        )

        response = requests.get(url)
        print("URL:", url)
        print("ステータスコード:", response.status_code)
        print("レスポンス:", response.text)

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

