# Ovoz orqali shaxsni aniqlovchi Telegram bot (aiogram 3)

Model: SpeechBrain ECAPA-TDNN · Baza: sizning `audios/` papkangiz

## Papka strukturasi
```
voice_id_bot/
├── audios/
│   ├── Ali_Valiyev/     (wav, mp3, ogg, m4a, flac ... istalgan format)
│   ├── Dilnoza_Karimova/
│   └── ...
├── bot.py  build_db.py  speaker_engine.py
```

## O'rnatish
```bash
sudo apt install ffmpeg            # Windows: ffmpeg.org dan o'rnating
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # BOT_TOKEN ni @BotFather dan oling
```

## Ishlatish
```bash
python build_db.py --root audios     # baza yaratish (audios o'zgarganda qayta ishga tushiring)
python bot.py                        # botni ishga tushirish
```

## Maslahatlar
- Har bir shaxs uchun kamida 5–10 ta, jami 1–2 daqiqa toza ovoz bo'lsin.
- Fon shovqini, musiqa yoki boshqa odam ovozi bo'lmasin.
- Noto'g'ri aniqlash ko'p bo'lsa `.env` da THRESHOLD ni oshiring (0.45–0.55), "topilmadi" ko'p chiqsa kamaytiring (0.30–0.35).
