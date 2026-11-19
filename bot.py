import asyncio
import os
import openpyxl
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Railway сам подставит эти значения из раздела Variables
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

EXCEL_FILE = "appointments.xlsx"

# Функция сохранения записи в Excel
def save_to_excel(name: str, service: str, date_time: str, phone: str):
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Записи"
        sheet.append(["Имя клиента", "Услуга", "Дата и время", "Телефон"])
        wb.save(EXCEL_FILE)

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active
    sheet.append([name, service, date_time, phone])
    wb.save(EXCEL_FILE)

# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✂️ Услуги и прайс"), KeyboardButton(text="📅 Записаться")],
        [KeyboardButton(text="📍 Адрес и график")]
    ],
    resize_keyboard=True
)

# Шаги анкеты записи
class BookingForm(StatesGroup):
    name = State()
    service = State()
    date_time = State()
    phone = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Добро пожаловать в барбершоп «STYLE». Выберите нужный раздел:",
        reply_markup=main_kb
    )

@dp.message(F.text == "✂️ Услуги и прайс")
async def show_prices(message: types.Message):
    text = (
        "<b>Наши услуги:</b>\n\n"
        "• Мужская стрижка — <b>1 500 ₽</b>\n"
        "• Моделирование бороды — <b>1 000 ₽</b>\n"
        "• Комплекс (стрижка + борода) — <b>2 200 ₽</b>\n"
        "• Детская стрижка — <b>1 100 ₽</b>"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📍 Адрес и график")
async def show_contacts(message: types.Message):
    await message.answer(
        "📍 Адрес: ул. Центральная, д. 15\n"
        "🕒 Работаем ежедневно с 10:00 до 21:00\n"
        "📞 Телефон: +7 (999) 000-00-00"
    )

# Запуск анкеты записи
@dp.message(F.text == "📅 Записаться")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer("Как вас зовут?")
    await state.set_state(BookingForm.name)

@dp.message(BookingForm.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Какую услугу вы хотите выбрать?")
    await state.set_state(BookingForm.service)

@dp.message(BookingForm.service)
async def get_service(message: types.Message, state: FSMContext):
    await state.update_data(service=message.text)
    await message.answer("На какой день и время вас записать? (Например: Завтра в 16:00)")
    await state.set_state(BookingForm.date_time)

@dp.message(BookingForm.date_time)
async def get_datetime(message: types.Message, state: FSMContext):
    await state.update_data(date_time=message.text)
    await message.answer("Оставьте ваш номер телефона для подтверждения записи:")
    await state.set_state(BookingForm.phone)

@dp.message(BookingForm.phone)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    save_to_excel(data["name"], data["service"], data["date_time"], message.text)

    if ADMIN_ID:
        admin_text = (
            f"💈 <b>Новая запись на стрижку!</b>\n\n"
            f"👤 Клиент: {data['name']}\n"
            f"✂️ Услуга: {data['service']}\n"
            f"🕒 Время: {data['date_time']}\n"
            f"📞 Телефон: {message.text}\n"
            f"🔗 Telegram: @{message.from_user.username}"
        )
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")

    await message.answer("✅ Вы успешно записаны! Администратор скоро свяжется с вами для подтверждения.")
    await state.clear()

# Админ-команда для скачивания Excel-таблицы
@dp.message(Command("excel"))
async def send_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if os.path.exists(EXCEL_FILE):
        await message.answer_document(FSInputFile(EXCEL_FILE), caption="📊 Таблица всех записей")
    else:
        await message.answer("Записей пока нет.")

async def main():
    print("Бот барбершопа запущен на Railway!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())