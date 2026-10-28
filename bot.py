import asyncio
import logging
import os
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from speaker_engine import SpeakerEngine

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
DB_PATH = os.getenv("DB_PATH", "speakers_db.npz")
THRESHOLD = float(os.getenv("THRESHOLD", "0.35"))
MIN_SEC, MAX_SEC = 3, 60

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
engine: SpeakerEngine | None = None


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "👋 Salom! Men ovoz orqali shaxsni aniqlovchi botman.\n\n"
        "🎤 Menga ovozli xabar (voice) yoki audio yuboring — "
        "bazadagi qaysi shaxsga eng o'xshashini topib beraman.\n\n"
        "ℹ️ /help — yordam, /info — baza haqida"
    )


@dp.message(Command("help"))
async def help_(m: Message):
    await m.answer(
        f"Ovoz uzunligi {MIN_SEC}–{MAX_SEC} soniya bo'lsin. Ovoz qancha toza va uzun bo'lsa, "
        "natija shuncha aniq bo'ladi.\n"
        "Bot faqat bazaga qo'shilgan shaxslarni taniydi."
    )


@dp.message(Command("info"))
async def info(m: Message):
    names = ", ".join(str(n) for n in engine.names)
    await m.answer(f"📚 Bazada {len(engine.names)} ta shaxs bor:\n{names}\n\n🎯 Chegara: {THRESHOLD}")


@dp.message(F.voice | F.audio | F.video_note)
async def handle_audio(m: Message, bot: Bot):
    media = m.voice or m.audio or m.video_note
    dur = media.duration or 0
    if dur < MIN_SEC:
        return await m.answer(f"⚠️ Ovoz juda qisqa (kamida {MIN_SEC} soniya kerak).")
    if dur > MAX_SEC:
        return await m.answer(f"⚠️ Ovoz juda uzun (ko'pi bilan {MAX_SEC} soniya).")

    wait = await m.answer("⏳ Tahlil qilinmoqda...")
    with tempfile.TemporaryDirectory() as tmp:
        src = str(Path(tmp) / "in.bin")
        try:
            await bot.download(media, destination=src)
            results = await asyncio.to_thread(engine.identify, src, 3)
        except Exception as e:
            logging.exception("Xato")
            return await wait.edit_text(f"❌ Xatolik: {e}")

    name, score = results[0]
    lines = []
    if score >= THRESHOLD:
        lines.append(f"✅ <b>Aniqlandi:</b> {name}\n📊 O'xshashlik: <b>{score:.1%}</b>")
    else:
        lines.append(
            f"❓ <b>Bazada mos shaxs topilmadi.</b>\n"
            f"Eng yaqini: {name} ({score:.1%}), chegaradan past."
        )
    lines.append("\n🏆 <b>Top-3:</b>")
    for i, (n, sc) in enumerate(results, 1):
        lines.append(f"{i}. {n} — {sc:.1%}")
    await wait.edit_text("\n".join(lines), parse_mode="HTML")


@dp.message()
async def fallback(m: Message):
    await m.answer("🎤 Iltimos, ovozli xabar yoki audio fayl yuboring.")


async def main():
    global engine
    engine = SpeakerEngine(DB_PATH)
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
