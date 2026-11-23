import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    ChatPermissions
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "9195945043:AAHaGUM-mjAhmtMFXu8o_zWUcooT-SLvPlA"

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings = {}
group_settings = {}

BAD_WORDS = ["reklama", "sotaman", "olaman", "kanalimga", "obuna", "skachat", "реклама", "продам", "куплю"]

class AdminStates(StatesGroup):
    waiting_for_channel = State()

def get_group_config(chat_id: int):
    if chat_id not in group_settings:
        group_settings[chat_id] = {
            "night_mode": False,
            "force_channel": None,
            "lang": "uz"
        }
    return group_settings[chat_id]

# --- LUG'AT (DICTIONARY) - O'ZBEK VA RUS TILLARI UCHUN ---
TEXTS = {
    "uz": {
        "features": (
            "⚙️ **DonTex Pro — Barcha imkoniyatlar:**\n\n"
            "**1. ⚙️ Asosiy Himoya va Filtrlar**\n"
            "• 🔗 **Anti-Link:** Tashqi va kanal havolalarini o'chiradi.\n"
            "• 🚫 **Bad Words:** So'kinish va reklamalarni to'sadi.\n"
            "• 🛡 **Channel Shield:** Kanal nomidan yozishni taqiqlaydi.\n"
            "• 🖼 **Media & Emoji Filter:** Stiker, GIF va ko'p emojilarni cheklaydi.\n\n"
            "**2. ⚠️ Intizom va Jazo Tizimi**\n"
            "• ⚠️ Qoidabuzarlarga ogohlantirish beradi (`1/3`, `2/3`).\n"
            "• 🔇 3 marta qoida buzganlarni **5 daqiqaga mute** qiladi.\n\n"
            "**3. 🚀 Tijoriy va Maxsus Imkoniyatlar**\n"
            "• 📢 **Force Subscribe:** Guruhga yozish uchun homiy kanalga obuna bo'lishni majburiy qiladi.\n"
            "• 🌙 **Night Mode:** Kechasi guruhda yozishni vaqtincha to'xtatib turadi.\n"
            "• 🌐 **Multi-language:** O'zbek va rus tillarini qo'llab-quvvatlaydi.\n"
            "• ⚙️ **Guruh Boshqaruv Paneli (`/settings`):** Barcha sozlamalar tugmalar orqali boshqariladi.\n\n"
            "**4. 👋 Kutib Olish Tizimi**\n"
            "• Yangi a'zolarni iliq kutib olib, qoidalarni eslatadi."
        ),
        "guide": (
            "📖 **Foydalanish bo'yicha qo'llanma:**\n\n"
            "1. Botni guruhga qo'shing va **Administrator** huquqini bering.\n"
            "2. Guruh ichida **`/settings`** deb yozing.\n"
            "3. Chiqqan chiroyli tugmalar yordamida Tungi rejim, Majburiy obuna va Tilni bir bosishda sozlang!"
        ),
        "btn_features": "⚙️ Asosiy funksiyalar",
        "btn_guide": "📖 Qo'llanma",
        "btn_start": "🔄 Bosh menyu (/start)",
        "btn_lang": "🇺🇿 / 🇷🇺 Tilni o'zgartirish",
        "btn_add_group": "➕ Guruhga qo'shish",
        "btn_back": "⬅️ Orqaga",
        "menu_text": "Tezkor boshqaruv menyusi:",
        "start_text": (
            "🛡 **DonTex Pro — Guruh Nazoratchisi va Himoya Tizimi**\n\n"
            "Botimiz guruhingizni har qanday keraksiz kontent va spamlardan 24/7 rejimida himoya qiladi.\n\n"
            "Meni guruhingizga qo'shing, Admin qiling va guruh ichida **/settings** buyrug'ini bosing!"
        ),
        "private_only": "⚠️ Bu buyruq faqat guruh ichida ishlaydi!",
        "not_admin": "❌ Faqat guruh adminlari o'zgartira oladi!",
        "panel_title": "⚙️ **{title}** guruhi boshqaruv paneli:\n\nKerakli sozlamani o'zgartirish uchun tugmani bosing 👇",
        "night_on": "✅ Yoqilgan",
        "night_off": "❌ O'chirilgan",
        "channel_not_connected": "❌ Ulanmagan",
        "night_label": "🌙 Tungi rejim: ",
        "channel_label": "📢 Majburiy obuna: ",
        "lang_label": "🌐 Til: 🇺🇿 O'zbekcha",
        "close_panel": "❌ Panelni yopish",
        "night_toggled": "Tungi rejim {status}",
        "lang_changed": "✅ Til o'zgartirildi: O'zbekcha 🇺🇿",
        "channel_info": "📢 Hozir ulangan kanal: **{channel}**\nNima qilamiz?",
        "remove_channel_btn": "🗑 Majburiy obunani o'chirish",
        "change_channel_btn": "🔄 Boshqa kanal ulash",
        "setup_channel_prompt": "📢 **Majburiy obuna ulash:**\n\nHomiy kanalingiz username'ini yuboring (Masalan: `@kanal_nomi`):\n⚠️ *Eslatma: Bot o'sha kanalda ham Admin bo'lishi shart!*",
        "enter_channel_prompt": "📢 Yangi kanal username'ini yuboring (Masalan: `@kanal`):",
        "channel_removed": "Majburiy obuna o'chirildi!",
        "panel_closed": "Panel yopildi",
        "channel_error_at": "⚠️ Xato! Kanal `@` belgisi bilan boshlanishi kerak (Masalan: `@kanal`). Qaytadan yuboring:",
        "channel_not_admin": "⚠️ **Xatolik!** Bot **{channel}** kanalida Admin emas!\nAvval botni kanalga Administrator qilib qo'shing, keyin qaytadan yuboring:",
        "channel_not_found": "⚠️ **{channel}** kanali topilmadi yoki bot u yerga qo'shilmagan!\nKanal ommaviy (Public) ekanligini va bot Admin qilinganini tekshirib, qaytadan yuboring:",
        "channel_success": "✅ **{channel} kanali majburiy obunaga muvaffaqiyatli ulandi!**\n\n⚙️ **{title}** boshqaruv paneli:",
        "welcome": "Salom, {name}! Guruhimizga xush kelibsiz. 😊\nIltimos, qoidalarga rioya qiling!",
        "night_active": "🌙 {name}, hozir Tungi rejim faol!",
        "sub_required": "❌ {name}, guruhda yozish uchun avval kanalga obuna bo'ling!",
        "btn_subscribe": "📢 Kanalga obuna bo'lish",
        "btn_check": "🔄 Tekshirish",
        "link_reason": "havola",
        "word_reason": "taqiqlangan so'z",
        "warn_msg": "⚠️ {name}, {reason} yuborish taqiqlangan! Ogohlantirish: {count}/3",
        "mute_msg": "🔇 {name} 3 marta qoida buzgani uchun 5 daqiqaga mute qilindi!",
        "sub_alert_not": "❌ Siz hali kanalga obuna bo'lmadingiz!",
        "sub_alert_yes": "✅ Obunangiz tasdiqlandi! Endi yozishingiz mumkin.",
        "sub_error": "⚠️ Xatolik yuz berdi. Bot kanalda admin ekanligini tekshiring.",
        "no_channel_set": "⚠️ Majburiy kanal belgilanmagan."
    },
    "ru": {
        "features": (
            "⚙️ **DonTex Pro — Все возможности:**\n\n"
            "**1. ⚙️ Основная защита и фильтры**\n"
            "• 🔗 **Anti-Link:** Удаляет внешние ссылки и ссылки на каналы.\n"
            "• 🚫 **Bad Words:** Блокирует мат и рекламу.\n"
            "• 🛡 **Channel Shield:** Запрещает писать от имени канала.\n"
            "• 🖼 **Media & Emoji Filter:** Ограничивает стикеры, GIF и много эмодзи.\n\n"
            "**2. ⚠️ Система дисциплины и наказаний**\n"
            "• ⚠️ Выдает предупреждения нарушителям (`1/3`, `2/3`).\n"
            "• 🔇 Дает **мут на 5 минут** тем, кто нарушил правила 3 раза.\n\n"
            "**3. 🚀 Коммерческие и особые функции**\n"
            "• 📢 **Force Subscribe:** Требует обязательную подписку на спонсорский канал для отправки сообщений.\n"
            "• 🌙 **Night Mode:** Временно отключает отправку сообщений в группе ночью.\n"
            "• 🌐 **Multi-language:** Поддержка узбекского и русского языков.\n"
            "• ⚙️ **Панель управления (`/settings`):** Все настройки управляются через кнопки.\n\n"
            "**4. 👋 Система приветствия**\n"
            "• Тепло приветствует новых участников и напоминает правила."
        ),
        "guide": (
            "📖 **Инструкция по использованию:**\n\n"
            "1. Добавьте бота в группу и дайте права **Администратора**.\n"
            "2. Напишите в группе команду **`/settings`**.\n"
            "3. Настройте Ночной режим, Обязательную подписку и Язык в один клик с помощью красивых кнопок!"
        ),
        "btn_features": "⚙️ Основные функции",
        "btn_guide": "📖 Инструкция",
        "btn_start": "🔄 Главное меню (/start)",
        "btn_lang": "🇺🇿 / 🇷🇺 Сменить язык",
        "btn_add_group": "➕ Добавить в группу",
        "btn_back": "⬅️ Назад",
        "menu_text": "Меню быстрого управления:",
        "start_text": (
            "🛡 **DonTex Pro — Модератор группы и система защиты**\n\n"
            "Наш бот защищает вашу группу от любого ненужного контента и спама 24/7.\n\n"
            "Добавьте меня в группу, сделайте администратором и отправьте команду **/settings**!"
        ),
        "private_only": "⚠️ Эта команда работает только внутри группы!",
        "not_admin": "❌ Только администраторы группы могут изменять настройки!",
        "panel_title": "⚙️ Панель управления группы **{title}**:\n\nНажмите кнопку для изменения настройки 👇",
        "night_on": "✅ Включен",
        "night_off": "❌ Отключен",
        "channel_not_connected": "❌ Не подключен",
        "night_label": "🌙 Ночной режим: ",
        "channel_label": "📢 Обязательная подписка: ",
        "lang_label": "🌐 Язык: 🇷🇺 Русский",
        "close_panel": "❌ Закрыть панель",
        "night_toggled": "Ночной режим {status}",
        "lang_changed": "✅ Язык изменен: Русский 🇷🇺",
        "channel_info": "📢 Текущий канал: **{channel}**\nЧто делаем?",
        "remove_channel_btn": "🗑 Отключить обязательную подписку",
        "change_channel_btn": "🔄 Подключить другой канал",
        "setup_channel_prompt": "📢 **Подключение обязательной подписки:**\n\nОтправьте юзернейм спонсорского канала (Например: `@channel_name`):\n⚠️ *Примечание: Бот должен быть Администратором в этом канале!*",
        "enter_channel_prompt": "📢 Отправьте юзернейм нового канала (Например: `@channel`):",
        "channel_removed": "Обязательная подписка отключена!",
        "panel_closed": "Панель закрыта",
        "channel_error_at": "⚠️ Ошибка! Юзернейм должен начинаться с `@` (Например: `@channel`). Отправьте заново:",
        "channel_not_admin": "⚠️ **Ошибка!** Бот не является Админом в канале **{channel}**!\nСначала добавьте бота в канал Администратором, затем отправьте заново:",
        "channel_not_found": "⚠️ Канал **{channel}** не найден или бот не добавлен туда!\nУбедитесь, что канал публичный и бот назначен Администратором, затем отправьте заново:",
        "channel_success": "✅ **Канал {channel} успешно подключен к обязательной подписке!**\n\n⚙️ Панель управления **{title}**:",
        "welcome": "Привет, {name}! Добро пожаловать в нашу группу. 😊\nПожалуйста, соблюдайте правила!",
        "night_active": "🌙 {name}, сейчас активен Ночной режим!",
        "sub_required": "❌ {name}, чтобы писать в группе, подпишитесь на канал!",
        "btn_subscribe": "📢 Подписаться на канал",
        "btn_check": "🔄 Проверить",
        "link_reason": "ссылка",
        "word_reason": "запрещенное слово",
        "warn_msg": "⚠️ {name}, отправка {reason} запрещена! Предупреждение: {count}/3",
        "mute_msg": "🔇 {name} получил мут на 5 минут за нарушение правил 3 раза!",
        "sub_alert_not": "❌ Вы еще не подписались на канал!",
        "sub_alert_yes": "✅ Подписка подтверждена! Теперь вы можете писать.",
        "sub_error": "⚠️ Произошла ошибка. Проверьте, является ли бот админом в канале.",
        "no_channel_set": "⚠️ Обязательный канал не установлен."
    }
}

def get_text(chat_id: int, key: str, **kwargs):
    cfg = get_group_config(chat_id)
    lang = cfg["lang"]
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, TEXTS["uz"][key])
    if kwargs:
        return text.format(**kwargs)
    return text

# --- SHAXSIY CHAT TUGMALARI ---
def get_main_reply_keyboard(chat_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(chat_id, "btn_features")), KeyboardButton(text=get_text(chat_id, "btn_guide"))],
            [KeyboardButton(text=get_text(chat_id, "btn_lang")), KeyboardButton(text=get_text(chat_id, "btn_start"))]
        ],
        resize_keyboard=True
    )

def get_inline_keyboard(chat_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(chat_id, "btn_features"), callback_data="features")],
            [InlineKeyboardButton(text=get_text(chat_id, "btn_guide"), callback_data="guide")],
            [InlineKeyboardButton(text=get_text(chat_id, "btn_add_group"), url="https://t.me/DonTex_bot?startgroup=true")]
        ]
    )

# --- GURUH BOSHQARUV PANELI ---
def get_admin_panel_keyboard(chat_id: int):
    cfg = get_group_config(chat_id)
    lang = cfg["lang"]
    
    if lang == "uz":
        night_status = "✅ Yoqilgan" if cfg["night_mode"] else "❌ O'chirilgan"
        lang_status = "🇺🇿 O'zbekcha"
    else:
        night_status = "✅ Включен" if cfg["night_mode"] else "❌ Отключен"
        lang_status = "🇷🇺 Русский"
        
    channel_status = cfg["force_channel"] if cfg["force_channel"] else get_text(chat_id, "channel_not_connected")

    night_prefix = "🌙 Tungi rejim: " if lang == "uz" else "🌙 Ночной режим: "
    channel_prefix = "📢 Majburiy obuna: " if lang == "uz" else "📢 Обязательная подписка: "
    lang_prefix = "🌐 Til: " if lang == "uz" else "🌐 Язык: "
    close_text = "❌ Panelni yopish" if lang == "uz" else "❌ Закрыть панель"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{night_prefix}{night_status}", callback_data="toggle_night")],
            [InlineKeyboardButton(text=f"{channel_prefix}{channel_status}", callback_data="setup_channel")],
            [InlineKeyboardButton(text=f"{lang_prefix}{lang_status}", callback_data="toggle_lang")],
            [InlineKeyboardButton(text=close_text, callback_data="close_panel")]
        ]
    )

# --- START VA MENYU ---
@dp.message(CommandStart())
@dp.message(F.text.in_(["🔄 Bosh menyu (/start)", "🔄 Главное меню (/start)"]))
async def start_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer(
            get_text(message.chat.id, "start_text"),
            reply_markup=get_main_reply_keyboard(message.chat.id),
            parse_mode="Markdown"
        )
        await message.answer(get_text(message.chat.id, "menu_text"), reply_markup=get_inline_keyboard(message.chat.id))

@dp.message(F.text.in_(["🇺🇿 / 🇷🇺 Tilni o'zgartirish", "🇺🇿 / 🇷🇺 Сменить язык"]))
async def change_personal_lang(message: Message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        cfg = get_group_config(chat_id)
        cfg["lang"] = "ru" if cfg["lang"] == "uz" else "uz"
        
        await message.answer(
            get_text(chat_id, "lang_changed"),
            reply_markup=get_main_reply_keyboard(chat_id)
        )
        # Menyu matnlarini yangi tilda chiqarish uchun
        await message.answer(get_text(chat_id, "menu_text"), reply_markup=get_inline_keyboard(chat_id))

@dp.message(F.text.in_(["⚙️ Asosiy funksiyalar", "⚙️ Основные функции"]))
async def reply_features(message: Message):
    if message.chat.type == "private":
        await message.answer(get_text(message.chat.id, "features"), parse_mode="Markdown")

@dp.message(F.text.in_(["📖 Qo'llanma", "📖 Инструкция"]))
async def reply_guide(message: Message):
    if message.chat.type == "private":
        await message.answer(get_text(message.chat.id, "guide"), parse_mode="Markdown", reply_markup=get_inline_keyboard(message.chat.id))

# --- GURUHDA /settings Yozilganda ---
@dp.message(Command("settings"))
async def open_group_settings(message: Message):
    if message.chat.type == "private":
        await message.answer(get_text(message.chat.id, "private_only"))
        return
        
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        try:
            await message.delete()
        except:
            pass
        return

    try:
        await message.delete()
    except:
        pass

    chat_id = message.chat.id
    await message.answer(
        get_text(chat_id, "panel_title", title=message.chat.title),
        reply_markup=get_admin_panel_keyboard(chat_id),
        parse_mode="Markdown"
    )

# --- CALLBACK TUGMALARNI BOSHQARISH ---
@dp.callback_query()
async def handle_all_callbacks(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    chat_id = callback.message.chat.id
    lang = get_group_config(chat_id)["lang"]
    back_text = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"

    if data == "features":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=back_text, callback_data="back")]])
        await callback.message.edit_text(get_text(chat_id, "features"), reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
        return
    elif data == "guide":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=back_text, callback_data="back")]])
        await callback.message.edit_text(get_text(chat_id, "guide"), reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
        return
    elif data == "back":
        await callback.message.edit_text(get_text(chat_id, "menu_text"), reply_markup=get_inline_keyboard(chat_id))
        await callback.answer()
        return

    # Obunani tekshirish tugmasi bosilganda
    elif data == "check_subscription":
        cfg = get_group_config(chat_id)
        channel_username = cfg.get("force_channel")
        if not channel_username:
            await callback.answer(get_text(chat_id, "no_channel_set"), show_alert=True)
            return
        try:
            user_status = await bot.get_chat_member(chat_id=channel_username, user_id=callback.from_user.id)
            if user_status.status in ["left", "kicked"]:
                await callback.answer(get_text(chat_id, "sub_alert_not"), show_alert=True)
            else:
                await callback.answer(get_text(chat_id, "sub_alert_yes"), show_alert=True)
                try:
                    await callback.message.delete()
                except:
                    pass
        except Exception as e:
            logging.error(f"Check subscription xatosi: {e}")
            await callback.answer(get_text(chat_id, "sub_error"), show_alert=True)
        return

    # Guruh admin paneli tekshiruvi
    member = await callback.message.chat.get_member(callback.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await callback.answer(get_text(chat_id, "not_admin"), show_alert=True)
        return

    cfg = get_group_config(chat_id)

    if data == "toggle_night":
        cfg["night_mode"] = not cfg["night_mode"]
        if cfg["lang"] == "uz":
            status = "yoqildi 🌙" if cfg["night_mode"] else "o'chirildi ☀️"
        else:
            status = "включен 🌙" if cfg["night_mode"] else "выключен ☀️"
            
        await callback.message.edit_reply_markup(reply_markup=get_admin_panel_keyboard(chat_id))
        await callback.answer(get_text(chat_id, "night_toggled", status=status))

    elif data == "toggle_lang":
        cfg["lang"] = "ru" if cfg["lang"] == "uz" else "uz"
        await callback.message.edit_reply_markup(reply_markup=get_admin_panel_keyboard(chat_id))
        await callback.answer(get_text(chat_id, "lang_changed"))

    elif data == "setup_channel":
        if cfg["force_channel"]:
            remove_text = "🗑 Majburiy obunani o'chirish" if cfg["lang"] == "uz" else "🗑 Отключить обязательную подписку"
            change_text = "🔄 Boshqa kanal ulash" if cfg["lang"] == "uz" else "🔄 Подключить другой канал"
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=remove_text, callback_data="remove_channel")],
                [InlineKeyboardButton(text=change_text, callback_data="enter_channel")],
                [InlineKeyboardButton(text=back_text, callback_data="back_panel")]
            ])
            await callback.message.edit_text(
                get_text(chat_id, "channel_info", channel=cfg['force_channel']),
                reply_markup=kb, parse_mode="Markdown"
            )
        else:
            await state.set_state(AdminStates.waiting_for_channel)
            await callback.message.edit_text(
                get_text(chat_id, "setup_channel_prompt"),
                parse_mode="Markdown"
            )
        await callback.answer()

    elif data == "enter_channel":
        await state.set_state(AdminStates.waiting_for_channel)
        await callback.message.edit_text(get_text(chat_id, "enter_channel_prompt"), parse_mode="Markdown")
        await callback.answer()

    elif data == "remove_channel":
        cfg["force_channel"] = None
        await callback.message.edit_text(
            get_text(chat_id, "panel_title", title=callback.message.chat.title),
            reply_markup=get_admin_panel_keyboard(chat_id), parse_mode="Markdown"
        )
        await callback.answer(get_text(chat_id, "channel_removed"))

    elif data == "back_panel":
        await callback.message.edit_text(
            get_text(chat_id, "panel_title", title=callback.message.chat.title),
            reply_markup=get_admin_panel_keyboard(chat_id), parse_mode="Markdown"
        )
        await callback.answer()

    elif data == "close_panel":
        await callback.message.delete()
        await callback.answer(get_text(chat_id, "panel_closed"))

@dp.message(AdminStates.waiting_for_channel)
async def save_channel_username(message: Message, state: FSMContext):
    chat_id = message.chat.id
    channel = message.text.strip()
    if not channel.startswith("@"):
        await message.answer(get_text(chat_id, "channel_error_at"))
        return

    try:
        chat_info = await bot.get_chat(channel)
        bot_member = await bot.get_chat_member(chat_id=channel, user_id=bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer(get_text(chat_id, "channel_not_admin", channel=channel), parse_mode="Markdown")
            return
    except Exception:
        await message.answer(get_text(chat_id, "channel_not_found", channel=channel), parse_mode="Markdown")
        return

    cfg = get_group_config(chat_id)
    cfg["force_channel"] = channel
    await state.clear()

    try:
        await message.delete()
    except:
        pass

    await message.answer(
        get_text(chat_id, "channel_success", channel=channel, title=message.chat.title),
        reply_markup=get_admin_panel_keyboard(chat_id),
        parse_mode="Markdown"
    )

# --- GURUH XABARLARINI HIMOYA QILISH ---
@dp.message(F.new_chat_members)
async def welcome_new_member(message: Message):
    chat_id = message.chat.id
    for member in message.new_chat_members:
        await message.reply(get_text(chat_id, "welcome", name=member.full_name))

@dp.message(F.sticker | F.animation)
async def filter_media(message: Message):
    if message.chat.type == "private":
        return
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in ["creator", "administrator"]:
            return
        await message.delete()
    except:
        pass

@dp.message(F.text)
async def filter_messages(message: Message):
    if message.chat.type == "private":
        return
        
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    text = message.text.lower()
    cfg = get_group_config(chat_id)
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status in ["creator", "administrator"]:
            return
        
        # 1. Tungi rejim
        if cfg["night_mode"]:
            await message.delete()
            await message.answer(get_text(chat_id, "night_active", name=user_name))
            return

        # 2. Majburiy obuna
        if cfg["force_channel"]:
            try:
                channel_username = cfg["force_channel"]
                user_status = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
                if user_status.status in ["left", "kicked"]:
                    await message.delete()
                    sub_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=get_text(chat_id, "btn_subscribe"), url=f"https://t.me/{channel_username.replace('@', '')}")],
                        [InlineKeyboardButton(text=get_text(chat_id, "btn_check"), callback_data="check_subscription")]
                    ])
                    await message.answer(get_text(chat_id, "sub_required", name=user_name), reply_markup=sub_kb)
                    return
            except Exception as e:
                logging.error(f"Force subscribe xatosi: {e}")

        # 3. Kanal nomidan yozish
        if message.sender_chat and message.sender_chat.id != chat_id:
            await message.delete()
            return

        # 4. Havolalar
        if "http://" in text or "https://" in text or "t.me/" in text:
            await message.delete()
            await handle_warning(message, user_id, user_name, get_text(chat_id, "link_reason"), cfg["lang"], chat_id)
            return

        # 5. Taqiqlangan so'zlar
        for word in BAD_WORDS:
            if word in text:
                await message.delete()
                await handle_warning(message, user_id, user_name, get_text(chat_id, "word_reason"), cfg["lang"], chat_id)
                return

        # 6. Ko'p emoji
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        if len(emoji_pattern.findall(message.text)) > 5:
            await message.delete()
            return

    except Exception as e:
        logging.error(f"Xabar filtrida xato: {e}")

async def handle_warning(message: Message, user_id: int, user_name: str, reason: str, lang: str, chat_id: int):
    warnings[user_id] = warnings.get(user_id, 0) + 1
    count = warnings[user_id]
    
    if count < 3:
        await message.answer(get_text(chat_id, "warn_msg", name=user_name, reason=reason, count=count))
    else:
        try:
            await message.chat.restrict(
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(asyncio.get_event_loop().time() + 300)
            )
            await message.answer(get_text(chat_id, "mute_msg", name=user_name))
            warnings[user_id] = 0
        except:
            pass

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Bosh menyu / Главное меню"),
        BotCommand(command="settings", description="Guruh sozlamalari / Настройки группы")
    ]
    await bot.set_my_commands(commands)

async def main():
    logging.basicConfig(level=logging.INFO)
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())