天気通知 LINE Bot
東京の天気を3時間ごとに通知する LINE Bot です。
Flask + LINE Messaging API + OpenWeather API で実装。

使用技術
Python 3.x

Flask

LINE Messaging API SDK

OpenWeatherMap API

Heroku

機能
「天気」とLINEに送ると、現在の天気＋3時間ごとの予報を返信

## 動作イメージ

ユーザー：
> 天気

Bot：
> 【現在の天気】
> 厚い雲、34.7℃
>
> 【3時間ごとの予報】
> 07/06 18:00: 曇り, 32℃
> 07/06 21:00: 雨, 28℃
> ...
