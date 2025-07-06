import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# 環境変数からキーを取得（Herokuなどの環境を想定）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
API_KEY = os.environ.get("WEATHER_API_KEY")
print(f"現在のAPI_KEY: {API_KEY}", flush=True)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 東京駅の座標例
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
        ### 現在の天気（Current Weather API）
        current_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
        )
        current_res = requests.get(current_url)

        if current_res.status_code == 200:
            current_data = current_res.json()
            current_weather = current_data["weather"][0]["description"]
            current_temp = current_data["main"]["temp"]
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="現在の天気情報の取得に失敗しました。")
            )
            return

        ### 予報（5日間/3時間ごと Forecast API）
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
        )
        forecast_res = requests.get(forecast_url)

        if forecast_res.status_code == 200:
            forecast_data = forecast_res.json()
            forecasts = forecast_data["list"][:5]  # 直近5件（3時間ごと × 5 = 15時間分）

            forecast_texts = []
            for item in forecasts:
                dt_txt = item["dt_txt"]  # 例: "2025-07-06 15:00:00"
                dt_utc = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")  # UTC時間としてパース
                dt_jst = dt_utc + timedelta(seconds=forecast_data["city"]["timezone"])  # JSTに変換（秒単位）
                time_str = dt_jst.strftime("%m/%d %H:%M")


                temp = item["main"]["temp"]
                weather_desc = item["weather"][0]["description"]

                forecast_texts.append(f"{time_str}: {weather_desc}, {temp}℃")

            hourly_info = "\n".join(forecast_texts)

            reply_text = f"【現在の天気】\n{current_weather}、{current_temp}℃\n\n【3時間ごとの予報】\n{hourly_info}"

        else:
            reply_text = "天気予報の取得に失敗しました。"

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
