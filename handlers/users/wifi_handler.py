# wifi_handlers.py
import asyncio
import logging
from aiogram import types
from loader import dp, wifi_db, user_db, bot
from data.config import ADMINS  # list yoki set of super-admin telegram ids

logger = logging.getLogger(__name__)

# yordamchi: admin tekshiruvi (super-admin yoki sayt adminlari)
async def is_admin(telegram_id: int) -> bool:
    # super-admin (config)
    if telegram_id in ADMINS:
        return True

    # oddiy adminlar user_db orqali (sening user_db API: select_user va check_if_admin)
    try:
        user = await asyncio.to_thread(user_db.select_user, telegram_id=telegram_id)
        if not user:
            return False
        user_id = user[0]
        return await asyncio.to_thread(user_db.check_if_admin, user_id=user_id)
    except Exception as e:
        logger.exception("Error checking admin status: %s", e)
        return False


# /setwifi <new_password>  (faqat adminlar)
@dp.message_handler(commands=["setwifi"])
async def cmd_setwifi(message: types.Message):
    telegram_id = message.from_user.id
    if not await is_admin(telegram_id):
        await message.reply("❌ Sizda bunday ruxsat yoʻq.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply("Foydalanish: /setwifi <yangi_parol>\nMasalan: /setwifi mynewpass123")
        return

    new_pass = parts[1].strip()

    try:
        await asyncio.to_thread(wifi_db.set_password, new_pass, f"set by {telegram_id}")
        await message.reply("✅ Wi-Fi parol muvaffaqiyatli yangilandi.")
        logger.info("Wi-Fi password set by %s", telegram_id)
    except Exception as e:
        logger.exception("Error setting wifi password: %s", e)
        await message.reply("❌ Parolni saqlashda xatolik yuz berdi.")


# /delwifi  (faqat adminlar) - barcha parollarni o'chiradi (sen bitta global parol ishlatasan)
@dp.message_handler(commands=["delwifi"])
async def cmd_delwifi(message: types.Message):
    telegram_id = message.from_user.id
    if not await is_admin(telegram_id):
        await message.reply("❌ Sizda bunday ruxsat yoʻq.")
        return

    try:
        await asyncio.to_thread(wifi_db.remove_password)
        await message.reply("✅ Wi-Fi parol oʻchirildi.")
        logger.info("Wi-Fi password removed by %s", telegram_id)
    except Exception as e:
        logger.exception("Error removing wifi password: %s", e)
        await message.reply("❌ Parolni oʻchirishda xatolik yuz berdi.")


# /getwifi - foydalanuvchilar uchun (minimal)
@dp.message_handler(commands=["getwifi"])
async def cmd_getwifi(message: types.Message):
    try:
        pw = await asyncio.to_thread(wifi_db.get_password)
        if pw:
            await message.answer(f"🔐 Wi-Fi parol: <b>{pw}</b>", parse_mode="HTML")
        else:
            await message.answer("❌ Hozirda Wi-Fi parol saqlanmagan. Iltimos admin bilan bog'laning.")
    except Exception as e:
        logger.exception("Error fetching wifi password: %s", e)
        await message.answer("❌ Parolni olishda xatolik yuz berdi. Iltimos admin bilan bog'laning.")
