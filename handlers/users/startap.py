# bot.py  (Aiogram v2.25.2)
import os
from aiogram import  types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp,bot

# Savollar ro'yxati (siz bergan 37 savol)
QUESTIONS = [
    "Assalomu alaykum! Boshlaymizmi? (Ha / Yo'q) — agar Ha bo'lsa, davom etamiz.",
    "Ismingizni kiriting:",
    "Loyihangiz yoki startapingiz nomi:",
    "Shior yoki slogani (agar mavjud bo'lsa):",
    "Sizning startap g‘oyangiz nimadan iborat?",
    "Ushbu g‘oya qanday muammoni hal qiladi?",
    "Nima sababdan bu muammo dolzarb?",
    "Sizning yechimingiz nimadan iborat (qisqa va aniq)?",
    "Loyihangizda qanday innovatsion jihatlar mavjud?",
    "G‘oyangizni 1 jumla bilan ifodalang (pitch intro sifatida):",
    "Sizning maqsadli auditoriyangiz kimlar?",
    "Auditoriyangizning taxminiy yoshi va sohasi qanday?",
    "Hozirda bu muammoni yechuvchi raqobatchilar bormi?",
    "Raqobatchilardan sizning afzalligingiz nimada?",
    "Bozor hajmini yoki potensial foydalanuvchilar sonini baholay olasizmi?",
    "Sizning mahsulotingiz yoki xizmat turi qanday (ilova, platforma, qurilma, xizmat va boshqalar)?",
    "Foydalanuvchi uni qanday ishlatadi?",
    "Asosiy funksiyalarini sanab bering:",
    "Loyiha hozir qaysi bosqichda (g‘oya, MVP, test, ishga tushgan, daromad bosqichi):",
    "Loyiha jamoangizda kimlar bor? (rol va mutaxassislik bo‘yicha)",
    "Loyihadan qanday daromad olasiz? (monetizatsiya modeli)",
    "Har bir foydalanuvchi uchun o‘rtacha daromad qancha bo‘ladi?",
    "Loyihani moliyalashtirish manbalari nimalar (grant, investor, o‘z mablag‘)?",
    "Sizga qancha boshlang‘ich investitsiya kerak?",
    "Mablag‘ asosan nimaga sarflanadi (reklama, IT ishlab chiqish, jamoa va h.k.)?",
    "Keyingi 6 oyda erishmoqchi bo‘lgan maqsadlaringiz nimalar?",
    "1 yillik rivojlanish strategiyangiz bormi?",
    "Loyihani kengaytirish uchun qanday imkoniyatlar ko‘ryapsiz?",
    "Hamkorlik qilishni istagan tashkilot yoki kompaniyalar bormi?",
    "Kelajakda xalqaro bozorlarga chiqish rejangiz bormi?",
    "Loyihangiz ijtimoiy jihatdan qanday foyda keltiradi?",
    "Atrof-muhit yoki jamiyat uchun qanday ijobiy natija beradi?",
    "Loyiha BMTning barqaror rivojlanish maqsadlaridan (SDG) qaysilariga mos keladi?",
    "Loyihangizning eng katta yutug‘i yoki noyobligi nimada?",
    "Sizning ilhom manbaingiz kim yoki nima bo‘lgan?",
    "Pitchni yakunlovchi bir jumla bilan o‘zingizni ta’riflang (motivatsion):",
    "Aloqa ma’lumotlaringiz (telefon, email, ijtimoiy tarmoq):"
]

# FSM: bitta state — savollar davomida
class Survey(StatesGroup):
    waiting = State()

# Inline keyboard: Ha / Yo'q
def start_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha", callback_data="start_yes"),
        InlineKeyboardButton("❌ Yo'q", callback_data="start_no")
    )
    return kb

# /start handler
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Assalomu alaykum! Siz StartUp Pitch Botdasiz.\n"
        "Ushbu bot yordamida g‘oyangizni pitchga aylantirasiz.\n\n"
        "Boshlaymizmi?",
        reply_markup=start_keyboard()
    )
    # indeks 0 uchun tayyorlaymiz (tasdiq)
    await state.update_data(index=0, answers=[])

# Callback: start yes/no
@dp.callback_query_handler(lambda c: c.data in ["start_yes", "start_no"])
async def process_start_choice(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    if callback_query.data == "start_no":
        await callback_query.message.answer("Xo'p, kerak bo'lsa /start orqali qayta boshlang. 😊")
        await state.finish()
        return

    # Boshlash: so'ramoqchi bo'lgan birinchi haqiqiy savol QUESTIONS[1]
    await state.update_data(index=1, answers=[])
    await Survey.waiting.set()
    await callback_query.message.answer(QUESTIONS[1])

# Message handler: savollarga javob qabul qiladi
@dp.message_handler(state=Survey.waiting, content_types=types.ContentTypes.TEXT)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    index = data.get("index", None)
    if index is None:
        await message.answer("So'rovni boshlash uchun /start bosing.")
        return

    # saqlash
    answers = data.get("answers", [])
    user_text = message.text.strip()
    answers.append(user_text)
    await state.update_data(answers=answers)

    # keyingi indeks
    next_index = index + 1
    # QUESTIONS list length: len(QUESTIONS) e.g. 37
    if next_index < len(QUESTIONS):
        await state.update_data(index=next_index)
        await message.answer(QUESTIONS[next_index])
    else:
        # barcha savollar tugadi
        await state.finish()
        compiled = build_pitch(message.from_user.id, answers)

        # Telegramga xabar sifatida yuborish (agar juda uzun bo'lsa bo'linishi mumkin)
        try:
            await message.answer("📄 Sizning tayyor pitch hujjatingiz:\n\n" + compiled)
        except Exception:
            await message.answer("Pitch juda uzun — fayl sifatida yuboriladi.")

        # faylga yozib yuborish
        filename = f"pitch_{message.from_user.id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(compiled)

        # yuborish
        try:
            with open(filename, "rb") as f:
                await bot.send_document(chat_id=message.chat.id, document=InputFile(f, filename=filename))
        except Exception:
            await message.answer("Faylni yuborishda xatolik yuz berdi.")
        finally:
            try:
                os.remove(filename)
            except Exception:
                pass

        await message.answer("✅ Hamma savollar tugadi. Agar yangidan boshlamoqchi bo'lsangiz, /start ni bosing.")

# /cancel uchun handler
@dp.message_handler(commands=["cancel"], state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("So'rovnoma bekor qilindi. /start bilan qayta boshlashingiz mumkin.")

# Helper: pitch yaratish
def build_pitch(user_id: int, answers: list) -> str:
    lines = []
    # QUESTIONS[1..] correspond to answers[0..]
    for i, ans in enumerate(answers, start=1):
        q_text = QUESTIONS[i]
        lines.append(f"{i}. {q_text}\nJavob: {ans}\n")
    header = "=== STARTUP PITCH HULLOSI ===\n\n"
    body = "\n".join(lines)
    footer = f"\nBot tomonidan avtomatik shakllantirildi. (user_id: {user_id})\n"
    return header + body + footer

if __name__ == "__main__":
    print("Bot ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True)
