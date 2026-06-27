import os
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from utils.messages import get, build_summary, format_price
from utils.pricing import (
    get_all_routes,
    get_route_by_id,
    get_car_types,
    get_price,
    get_car_max_passengers,
    needs_deposit,
    get_deposit_amount,
    get_contact,
    get_bank_info,
    get_route_label,
    get_car_label,
)
from utils.user_store import register_user
from utils.validation import (
    validate_name,
    validate_flight,
    validate_time,
    normalize_time,
    validate_date,
    validate_phone,
    validate_whatsapp,
    normalize_whatsapp,
    validate_telegram,
    normalize_telegram,
)

(
    LANGUAGE,
    BOOKING_TYPE,
    ROUTE,
    CAR_TYPE,
    NAME,
    FLIGHT,
    BOOKING_DATE,
    ARRIVAL_TIME,
    PASSENGERS,
    CONTACT_METHOD,
    CONTACT_INFO,
    CONFIRM,
) = range(12)

ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))

_CONTACT_PROMPTS = {
    "phone": "enter_contact_phone",
    "whatsapp": "enter_contact_whatsapp",
    "telegram": "enter_contact_telegram",
}
_CONTACT_ERR = {
    "phone": "err_contact_phone",
    "whatsapp": "err_contact_whatsapp",
    "telegram": "err_contact_telegram",
}
_CONTACT_LABELS = {
    "phone": "📞",
    "whatsapp": "💬 WhatsApp",
    "telegram": "✈️ Telegram",
}


def _lang(ctx: ContextTypes.DEFAULT_TYPE) -> str:
    return ctx.user_data.get("lang", "vi")


def _vietqr_url(bank_id: str, account_number: str, account_name: str,
                amount: int, content: str) -> str:
    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_number}-compact2.png"
        f"?amount={amount}"
        f"&addInfo={urllib.parse.quote(content)}"
        f"&accountName={urllib.parse.quote(account_name)}"
    )


def _deposit_content(data: dict) -> str:
    name = data.get("name", "").upper().replace(" ", "")[:10]
    flight = data.get("flight", "")
    return f"DAT COC {name} {flight}"


# ─── Entry ───────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    register_user(update.effective_chat.id)
    kb = [[
        InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
    ]]
    await update.message.reply_text(
        get("welcome", "vi"),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LANGUAGE


async def choose_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = q.data.replace("lang_", "")
    ctx.user_data["lang"] = lang

    kb = [[
        InlineKeyboardButton(get("btn_book_now", lang), callback_data="btype_now"),
        InlineKeyboardButton(get("btn_book_scheduled", lang), callback_data="btype_scheduled"),
    ]]
    await q.edit_message_text(
        get("choose_booking_type", lang),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BOOKING_TYPE


async def choose_booking_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = _lang(ctx)
    ctx.user_data["booking_type"] = q.data.replace("btype_", "")

    routes = get_all_routes()
    kb = [[InlineKeyboardButton(get_route_label(r, lang), callback_data=f"route_{r['id']}")] for r in routes]
    await q.edit_message_text(
        get("choose_route", lang),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return ROUTE


# ─── Route / Car ─────────────────────────────────────────────────────────────

async def choose_route(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = _lang(ctx)
    route_id = q.data.replace("route_", "")
    route = get_route_by_id(route_id)
    ctx.user_data["route_id"] = route_id
    ctx.user_data["route_label"] = get_route_label(route, lang)

    car_types = get_car_types()
    kb = [[InlineKeyboardButton(info[f"label_{lang}"], callback_data=f"car_{ct}")] for ct, info in car_types.items()]
    await q.edit_message_text(get("choose_car", lang), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return CAR_TYPE


async def choose_car(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = _lang(ctx)
    car_type = q.data.replace("car_", "")
    ctx.user_data["car_type"] = car_type
    ctx.user_data["car_label"] = get_car_label(car_type, lang)
    ctx.user_data["price"] = get_price(ctx.user_data["route_id"], car_type)
    await q.edit_message_text(get("enter_name", lang), parse_mode="Markdown")
    return NAME


# ─── Text steps with validation ──────────────────────────────────────────────

async def enter_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    text = update.message.text.strip()
    if not validate_name(text):
        await update.message.reply_text(get("err_name", lang), parse_mode="Markdown")
        return NAME
    ctx.user_data["name"] = text
    await update.message.reply_text(get("enter_flight", lang), parse_mode="Markdown")
    return FLIGHT


async def enter_flight(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    text = update.message.text.strip().upper()
    if not validate_flight(text):
        await update.message.reply_text(get("err_flight", lang), parse_mode="Markdown")
        return FLIGHT
    ctx.user_data["flight"] = text

    if ctx.user_data.get("booking_type") == "scheduled":
        await update.message.reply_text(get("enter_booking_date", lang), parse_mode="Markdown")
        return BOOKING_DATE

    await update.message.reply_text(get("enter_arrival_time", lang), parse_mode="Markdown")
    return ARRIVAL_TIME


async def enter_booking_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    text = update.message.text.strip()
    ok, result = validate_date(text)
    if not ok:
        err_key = "err_date_past" if result == "past" else "err_date_invalid"
        await update.message.reply_text(get(err_key, lang), parse_mode="Markdown")
        return BOOKING_DATE
    ctx.user_data["booking_date"] = result
    await update.message.reply_text(get("enter_arrival_time", lang), parse_mode="Markdown")
    return ARRIVAL_TIME


async def enter_arrival_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    text = update.message.text.strip()
    if not validate_time(text):
        await update.message.reply_text(get("err_time", lang), parse_mode="Markdown")
        return ARRIVAL_TIME
    ctx.user_data["arrival_time"] = normalize_time(text)
    await update.message.reply_text(get("enter_passengers", lang), parse_mode="Markdown")
    return PASSENGERS


async def enter_passengers(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text(get("invalid_input", lang), parse_mode="Markdown")
        return PASSENGERS
    passengers = int(text)
    max_p = get_car_max_passengers(ctx.user_data["car_type"])
    if passengers > max_p:
        await update.message.reply_text(get("passengers_exceed", lang, max=max_p), parse_mode="Markdown")
        return PASSENGERS
    ctx.user_data["passengers"] = passengers

    kb = [
        [InlineKeyboardButton(get("btn_contact_phone", lang), callback_data="cmethod_phone")],
        [InlineKeyboardButton(get("btn_contact_whatsapp", lang), callback_data="cmethod_whatsapp")],
        [InlineKeyboardButton(get("btn_contact_telegram", lang), callback_data="cmethod_telegram")],
    ]
    await update.message.reply_text(
        get("choose_contact_method", lang),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return CONTACT_METHOD


async def choose_contact_method(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = _lang(ctx)
    method = q.data.replace("cmethod_", "")
    ctx.user_data["contact_method_key"] = method
    await q.edit_message_text(get(_CONTACT_PROMPTS[method], lang), parse_mode="Markdown")
    return CONTACT_INFO


async def enter_contact_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    raw = update.message.text.strip()
    method = ctx.user_data.get("contact_method_key", "phone")

    valid = False
    normalized = raw
    if method == "phone":
        valid = validate_phone(raw)
    elif method == "whatsapp":
        valid = validate_whatsapp(raw)
        if valid:
            normalized = normalize_whatsapp(raw)
    elif method == "telegram":
        valid = validate_telegram(raw)
        if valid:
            normalized = normalize_telegram(raw)

    if not valid:
        await update.message.reply_text(get(_CONTACT_ERR[method], lang), parse_mode="Markdown")
        return CONTACT_INFO

    ctx.user_data["contact_method"] = f"{_CONTACT_LABELS[method]}: {normalized}"

    data = ctx.user_data
    summary = build_summary(data, lang, data["route_label"], data["car_label"])
    kb = [[
        InlineKeyboardButton(get("btn_confirm", lang), callback_data="booking_confirm"),
        InlineKeyboardButton(get("btn_cancel", lang), callback_data="booking_cancel"),
    ]]
    await update.message.reply_text(
        get("confirm_booking", lang, summary=summary),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return CONFIRM


# ─── Confirm ─────────────────────────────────────────────────────────────────

async def confirm_booking(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = _lang(ctx)
    data = ctx.user_data
    contact = get_contact()

    if q.data == "booking_cancel":
        await q.edit_message_text(get("booking_cancelled", lang), parse_mode="Markdown")
        return ConversationHandler.END

    customer_id = update.effective_user.id
    customer_name_tg = update.effective_user.full_name
    ctx.user_data["customer_id"] = customer_id

    price = data["price"]
    deposit_needed = needs_deposit(price)
    deposit_amt = get_deposit_amount()
    remaining = price - deposit_amt
    bank = get_bank_info()
    summary = build_summary(data, lang, data["route_label"], data["car_label"])

    if deposit_needed:
        await q.edit_message_text(
            get("booking_pending_deposit", lang,
                deposit=format_price(deposit_amt),
                remaining=format_price(remaining)),
            parse_mode="Markdown",
        )
        qr_content = _deposit_content(data)
        qr_url = _vietqr_url(bank["bank_id"], bank["account_number"],
                              bank["account_name"], deposit_amt, qr_content)
        await ctx.bot.send_photo(
            chat_id=customer_id,
            photo=qr_url,
            caption=get("deposit_qr_caption", lang,
                        content=qr_content,
                        deposit=format_price(deposit_amt),
                        bank_id=bank["bank_id"],
                        account_number=bank["account_number"],
                        account_name=bank["account_name"]),
            parse_mode="Markdown",
        )
    else:
        await q.edit_message_text(
            get("booking_confirmed_no_deposit", lang), parse_mode="Markdown"
        )

    await _send_thank_you(ctx, customer_id, lang)

    driver_summary = build_summary(data, "vi", data["route_label"], data["car_label"])
    driver_summary += f"\n👤 *TG:* [{customer_name_tg}](tg://user?id={customer_id})"
    if deposit_needed:
        driver_summary += f"\n💰 *Cọc:* {format_price(deposit_amt)} | *Còn lại:* {format_price(remaining)}"

    notify_key = "driver_notify_deposit" if deposit_needed else "driver_notify"
    driver_kb = [[
        InlineKeyboardButton(get("btn_accept", "vi"), callback_data=f"driver_accept_{customer_id}"),
        InlineKeyboardButton(get("btn_reject", "vi"), callback_data=f"driver_reject_{customer_id}"),
    ]]

    if ADMIN_CHAT_ID:
        await ctx.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=get(notify_key, "vi", summary=driver_summary),
            reply_markup=InlineKeyboardMarkup(driver_kb),
            parse_mode="Markdown",
        )
        ctx.bot_data.setdefault("pending_bookings", {})[str(customer_id)] = {
            "lang": lang,
            "summary": summary,
            "deposit_needed": deposit_needed,
            "deposit_confirmed": False,
        }

    return ConversationHandler.END


async def _send_thank_you(ctx: ContextTypes.DEFAULT_TYPE, customer_id: int, lang: str) -> None:
    kb = [[
        InlineKeyboardButton(get("btn_book_more", lang), callback_data="book_more_yes"),
        InlineKeyboardButton(get("btn_no_thanks", lang), callback_data="book_more_no"),
    ]]
    await ctx.bot.send_message(
        chat_id=customer_id,
        text=get("thank_you", lang),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


# ─── Book more ───────────────────────────────────────────────────────────────

async def book_more_response(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    await q.edit_message_reply_markup(reply_markup=None)

    if q.data == "book_more_yes":
        ctx.user_data.clear()
        kb = [[
            InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        ]]
        await ctx.bot.send_message(
            chat_id=update.effective_user.id,
            text=get("welcome", "vi"),
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )
        return LANGUAGE

    return ConversationHandler.END


# ─── Driver callbacks ─────────────────────────────────────────────────────────

async def driver_response(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    driver_name = update.effective_user.full_name
    parts = q.data.split("_")
    action = parts[1]
    customer_id = int(parts[2])
    contact = get_contact()

    pending = ctx.bot_data.get("pending_bookings", {})
    booking = pending.get(str(customer_id), {})
    lang = booking.get("lang", "vi")
    deposit_needed = booking.get("deposit_needed", False)

    if action == "accept":
        if deposit_needed:
            deposit_kb = [[InlineKeyboardButton(
                get("btn_deposit_confirmed", "vi"),
                callback_data=f"driver_deposit_{customer_id}"
            )]]
            await q.edit_message_text(
                get("driver_accepted_waiting_deposit", "vi"),
                reply_markup=InlineKeyboardMarkup(deposit_kb),
                parse_mode="Markdown",
            )
        else:
            await q.edit_message_text(
                get("driver_accepted_no_deposit", "vi", driver=driver_name),
                parse_mode="Markdown",
            )
            try:
                await ctx.bot.send_message(
                    chat_id=customer_id,
                    text=get("customer_driver_assigned", lang,
                             telegram=contact["telegram"],
                             whatsapp=contact["whatsapp"]),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    elif action == "reject":
        await q.edit_message_text(
            get("driver_rejected", "vi", driver=driver_name), parse_mode="Markdown"
        )

    elif action == "deposit":
        await q.edit_message_text(get("driver_deposit_done", "vi"), parse_mode="Markdown")
        if str(customer_id) in pending:
            pending[str(customer_id)]["deposit_confirmed"] = True
        try:
            await ctx.bot.send_message(
                chat_id=customer_id,
                text=get("booking_deposit_confirmed", lang,
                         telegram=contact["telegram"],
                         whatsapp=contact["whatsapp"]),
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(ctx)
    await update.message.reply_text(get("booking_cancelled", lang))
    return ConversationHandler.END


# ─── Handler builder ─────────────────────────────────────────────────────────

def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(book_more_response, pattern="^book_more_yes$"),
        ],
        states={
            LANGUAGE: [CallbackQueryHandler(choose_language, pattern="^lang_")],
            BOOKING_TYPE: [CallbackQueryHandler(choose_booking_type, pattern="^btype_")],
            ROUTE: [CallbackQueryHandler(choose_route, pattern="^route_")],
            CAR_TYPE: [CallbackQueryHandler(choose_car, pattern="^car_")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            FLIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_flight)],
            BOOKING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_booking_date)],
            ARRIVAL_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_arrival_time)],
            PASSENGERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_passengers)],
            CONTACT_METHOD: [CallbackQueryHandler(choose_contact_method, pattern="^cmethod_")],
            CONTACT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_info)],
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern="^booking_(confirm|cancel)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )
