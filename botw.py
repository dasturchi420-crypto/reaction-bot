import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    BotCommand
)
from aiogram.filters import CommandStart

# Bot tokeningiz
TOKEN = "8682338480:AAGvBLFyNA6mvprm97DUqO9L_OeEWbnDwuU"

# Reaksiyalar bosilganda xabar boradigan Admin Telegram ID si
ADMIN_ID = 7044084668

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Bot har xil qilib tanlashi uchun emojilar to'plami
EMOJI_POOL = ["👍", "❤️", "🔥", "🤩", "👏", "💯", "🎉", "⚡️", "😍", "🤝", "🚀", "💡"]

# Bosh menyu inline tugmalari
def get_start_keyboard(bot_username: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Kanalga qo'shish", 
                    url=f"https://t.me/{bot_username}?startchannel=true&admin=edit_messages"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 Qo'llanma va Yo'riqnoma", 
                    callback_data="help_instruction"
                )
            ]
        ]
    )

# /start buyrug'i uchun handler (Xatolik to'g'rilandi)
@dp.message(CommandStart())
async def start_cmd(message: Message):
    bot_info = await bot.get_me()
    text = (
        "<b>Assalomu alaykum! Men kanallarga avtomatik layk va reaksiyalar qo'shuvchi botman.</b>\n\n"
        "✨ <b>Imkoniyatlarim:</b>\n"
        "Kanalingizga yangi post joylanganda, avtomatik ravishda turli xil emojilardan iborat tugmalarni biriktirib beraman.\n\n"
        "👇 Botni kanalingizga sozlash uchun quyidagi tugmani bosing:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_start_keyboard(bot_info.username))

# Qo'llanma tugmasi bosilganda
@dp.callback_query(F.data == "help_instruction")
async def show_help(callback: CallbackQuery):
    instruction_text = (
        "📋 <b>Botni kanalga ulash bo'yicha yo'riqnoma:</b>\n\n"
        "1️⃣ Yuqoridagi <b>'➕ Kanalga qo'shish'</b> tugmasini bosing.\n"
        "2️⃣ Botingizni ulamoqchi bo'lgan kanalingizni tanlang.\n"
        "3️⃣ Botga adminlik huquqini tasdiqlang.\n"
        "4️⃣ Kanalingizga yangi post joylang — bot avtomatik tarzda turli xil emojili layk tugmalarini qo'shib beradi!"
    )
    await callback.message.answer(instruction_text, parse_mode="HTML")
    await callback.answer()

# Kanalga post joylanganda ishlovchi handler (4-5 ta emoji chiqaradi)
@dp.channel_post()
async def auto_like_channel_post(message: Message):
    # Har safar aniq 4 tadan 5 tagacha tasodifiy emoji tanlanadi
    chosen_emojis = random.sample(EMOJI_POOL, k=random.randint(4, 5))
    
    # Tugmalarni bir qatorda chiroyli qilib joylashtirish
    row_buttons = [
        InlineKeyboardButton(text=f"{emoji} 0", callback_data=f"like_{emoji}")
        for emoji in chosen_emojis
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[row_buttons])
    
    try:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Postga layk qo'shishda xatolik: {e}")

# Reaksiya tugmalari bosilganda sanoqni oshirish va Adminga bildirishnoma yuborish
@dp.callback_query(F.data.startswith("like_"))
async def handle_like(callback: CallbackQuery):
    emoji = callback.data.split("_")[1]
    
    if not callback.message or not callback.message.reply_markup:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
        return

    reply_markup = callback.message.reply_markup
    new_inline_keyboard = []

    for row in reply_markup.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data == callback.data:
                text_parts = btn.text.split(" ")
                current_count = int(text_parts[1]) if len(text_parts) > 1 and text_parts[1].isdigit() else 0
                new_text = f"{emoji} {current_count + 1}"
                new_row.append(InlineKeyboardButton(text=new_text, callback_data=btn.callback_data))
            else:
                new_row.append(btn)
        new_inline_keyboard.append(new_row)

    try:
        # 1. Post ostidagi tugmani yangilaymiz
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=new_inline_keyboard)
        )
        await callback.answer(f"Siz {emoji} reaksiyasini qoldirdingiz!")

        # 2. Tugmani bosgan foydalanuvchi haqida ADMINGA xabar yuborish
        user = callback.from_user
        username_text = f"@{user.username}" if user.username else "Mavjud emas"
        
        notification_text = (
            "🔔 <b>Yangi reaksiya bosildi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"🔗 <b>Username:</b> {username_text}\n"
            f"🎭 <b>Bosilgan reaksiya:</b> {emoji}"
        )
        
        # Adminga xabarnoma yuboramiz
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=notification_text, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Tugmani yangilashda xatolik: {e}")
        await callback.answer()

# Chat pastida ko'k menudagi komandalarni sozlash
async def set_main_menu(bot: Bot):
    main_commands = [
        BotCommand(command="start", description="Botni ishga tushirish va yo'riqnoma")
    ]
    await bot.set_my_commands(main_commands)

async def main():
    await set_main_menu(bot)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())