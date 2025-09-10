import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

API_TOKEN ="8176325880:AAEY3GpCwl2JIwWzyjJmwwS1VWd-wa0Tzbg"

ADMIN_ID = 1421622919  # Replace with the actual admin ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

#FSM holatlar
class ApplicationForm(StatesGroup):
    name = State()
    phone = State()
    role = State()
    content = State()

#Start komandasi
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}!\n"
                         "Iltimos, ism va familiyangizni kiriting:")
    await state.set_state(ApplicationForm.name)
    # Adminni xabardor qilish
    await bot.send_message(ADMIN_ID, f"Yangi foydalanuvchi botga start bosdi: {message.from_user.full_name} (ID: {message.from_user.id})")


# Ism va familiya qabul qilish
@dp.message(ApplicationForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Telefon raqamingizni kiriting (masalan: +998901234567):")
    await state.set_state(ApplicationForm.phone)
    # Adminni xabardor qilish

# telefon
@dp.message(ApplicationForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    
    role_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Talaba"), KeyboardButton(text="O'qituvchi")],
            [KeyboardButton(text="Boshqa")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Siz kim sifatida ariza topshiryapsiz?", reply_markup=role_keyboard)
    await state.set_state(ApplicationForm.role)

# Rol tanlash
@dp.message(ApplicationForm.role, F.text.in_({"Talaba", "O'qituvchi", "Boshqa"}))
async def process_role(message: Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer("Ariza mazmunini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ApplicationForm.content)

# Ariza mazmuni
@dp.message(ApplicationForm.content)
async def get_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    data = await state.get_data()

    # Telegram user ma'lumotlari
    tg_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Yo‘q"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    # Admin uchun xabar
    text = (
        f"📩 Yangi ariza!\n\n"
        f"👤 F.I.Sh: {data['name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"🏷 Rol: {data['role']}\n"
        f"📝 Ariza:\n{data['content']}\n\n"
        f"ℹ️ Telegram ma'lumotlari:\n"
        f"🆔 ID: {tg_id}\n"
        f"👤 Username: {username}\n"
        f"📛 Full Name: {full_name}"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=text)

    # Foydalanuvchiga javob
    await message.answer("✅ Arizangiz adminga yuborildi. Rahmat!")

    await state.clear()

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

