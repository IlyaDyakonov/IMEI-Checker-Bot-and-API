from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import asyncio
import logging
import sys

dp = Dispatcher()
bot = None

TOKEN = "YOUR_TELEGRAM_TOKEN"   #Впишите сюда токен Вашего телеграм бота.

# Белый список пользователей
WHITE_LIST = {485165808}  # ID разрешённых пользователей (через пробел). тип number

# Проверка доступа
async def is_allowed_user(user_id: int) -> bool:
    return user_id in WHITE_LIST

# Переключение между Sandbox и Live
class IMEIChecker:
    def __init__(self):
        self.use_sandbox = True

    def toggle_mode(self):
        self.use_sandbox = not self.use_sandbox

    def get_mode(self):
        return "Sandbox" if self.use_sandbox else "Live"

    async def query_imei_service(self, imei: str) -> str:
        if self.use_sandbox:
            # Режим Sandbox
            api_token_imei = "e4oEaZY1Kom5OXzybETkMlwjOCy3i8GSCGTHzWrhd4dc563b"
            api_url = "https://api.imeicheck.net/v1/checks"
            serviceId = 12
        else:
            # Режим Live
            api_token_imei = "sy5woSxuac7xKalljXFjgbB2hCRw7GQLueRtGp1974d8fe72"
            api_url = "https://api.imeicheck.net/v1/checks"
            serviceId = 1
        headers = {
            'Authorization': 'Bearer ' + api_token_imei,
            'Content-Type': 'application/json'
        }
        body = json.dumps({
            "deviceId": imei,
            "serviceId": serviceId,
        })
        response = requests.post(api_url, headers=headers, data=body)
        return response.text

imei_checker = IMEIChecker()

# команда старт
@dp.message(CommandStart())
async def on_startup(message: Message):
    if not await is_allowed_user(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    await message.answer_sticker('CAACAgIAAxkBAAEGKpBmbZyrUjIKtEHoz9yyqSR1-MnnxwACXQADQbVWDIidO3ORssYPNQQ')
    await message.answer(f"Добро пожаловать! Отправьте IMEI для проверки.\nТекущий режим: {imei_checker.get_mode()}\nДля смены режима нажмите /switch_mode")

# Команда для переключения режима
@dp.message(Command(commands=["switch_mode"]))
async def switch_mode(message: Message):
    imei_checker.toggle_mode()
    await message.answer(f"Режим работы изменён на: {imei_checker.get_mode()}")

# Обработчик команды проверки IMEI
@dp.message()
async def check_imei(message: Message):
    if not await is_allowed_user(message.from_user.id):
        await message.answer("Вам запрещён доступ к боту.")
        return
    imei = message.text.strip()
    if not imei.isdigit() or len(imei) not in (14, 15):
        await message.answer("Некорректный IMEI. Введите 14 или 15 цифр.")
        return
    result = await imei_checker.query_imei_service(imei)
    formatted_result = json.dumps(json.loads(result), indent=4, ensure_ascii=False)
    await message.answer(f"Результат проверки IMEI {imei}:\n<pre>{formatted_result}</pre>", parse_mode=ParseMode.HTML)


async def main() -> None:
	global bot

	bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
	await dp.start_polling(bot)

if __name__ == "__main__":
	try:
		logging.basicConfig(level=logging.INFO, stream=sys.stdout)
		asyncio.run(main())
	except KeyboardInterrupt:
		print('Exit')


# FastAPI сервис для обработки внешних запросов
app = FastAPI()

class IMEIRequest(BaseModel):
    imei: str
    token: str

@app.post("/api/check-imei")
async def check_imei_api(request: IMEIRequest):
    API_TOKEN = "PythonForever!"
    if request.token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Неверный токен")
    if not request.imei.isdigit() or len(request.imei) not in (14, 15):
        raise HTTPException(status_code=400, detail="Некорректный IMEI")
    result = await imei_checker.query_imei_service(request.imei)
    return {"imei": request.imei, "result": json.loads(result)}