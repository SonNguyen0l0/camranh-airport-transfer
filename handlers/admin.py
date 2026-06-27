import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.user_store import get_all_users, get_user_count

ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))


def _is_admin(update: Update) -> bool:
    uid = update.effective_user.id
    cid = update.effective_chat.id
    return uid == ADMIN_CHAT_ID or cid == ADMIN_CHAT_ID


async def admin_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text("⛔ Bạn không có quyền truy cập lệnh này.")
        return

    pending = ctx.bot_data.get("pending_bookings", {})

    if not pending:
        await update.message.reply_text(
            "📋 *DANH SÁCH ĐƠN*\n\nKhông có đơn nào đang chờ xử lý.",
            parse_mode="Markdown",
        )
        return

    lines = ["📋 *DANH SÁCH ĐƠN ĐANG CHỜ*\n"]
    total = len(pending)
    waiting_deposit = 0

    for i, (cid, booking) in enumerate(pending.items(), 1):
        dep_needed = booking.get("deposit_needed", False)
        dep_confirmed = booking.get("deposit_confirmed", False)
        lang = booking.get("lang", "vi")

        if dep_needed and not dep_confirmed:
            status = "⏳ Chờ cọc"
            waiting_deposit += 1
        elif dep_needed and dep_confirmed:
            status = "✅ Đã cọc"
        else:
            status = "✅ Xác nhận"

        summary_short = booking.get("summary", "").split("\n")
        route = next((l for l in summary_short if "Tuyến" in l or "Route" in l or "Маршрут" in l), "")
        name = next((l for l in summary_short if "Họ tên" in l or "Name" in l or "Имя" in l), "")
        flight = next((l for l in summary_short if "Chuyến bay" in l or "Flight" in l or "Рейс" in l), "")

        lines.append(
            f"*{i}.* {status}\n"
            f"   {route.strip()}\n"
            f"   {name.strip()}\n"
            f"   {flight.strip()}\n"
            f"   🌐 Lang: `{lang}` | ID: `{cid}`\n"
        )

    lines.append(f"\n📊 Tổng: *{total}* đơn | ⏳ Chờ cọc: *{waiting_deposit}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def admin_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text("⛔ Bạn không có quyền truy cập lệnh này.")
        return

    count = len(ctx.bot_data.get("pending_bookings", {}))
    ctx.bot_data["pending_bookings"] = {}
    await update.message.reply_text(
        f"🗑 Đã xoá *{count}* đơn khỏi danh sách.",
        parse_mode="Markdown",
    )


async def admin_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text("⛔ Bạn không có quyền truy cập lệnh này.")
        return

    count = get_user_count()
    await update.message.reply_text(
        f"👥 *Tổng khách hàng đã đăng ký:* *{count}* người",
        parse_mode="Markdown",
    )


async def admin_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text("⛔ Bạn không có quyền truy cập lệnh này.")
        return

    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text(
            "⚠️ Cú pháp: `/broadcast <nội dung tin nhắn>`\n\n"
            "Ví dụ:\n`/broadcast 🎉 Chúng tôi có khuyến mãi 20% hôm nay!`",
            parse_mode="Markdown",
        )
        return

    users = get_all_users()
    total = len(users)

    if total == 0:
        await update.message.reply_text("📭 Chưa có khách hàng nào trong danh sách.")
        return

    await update.message.reply_text(
        f"📤 Đang gửi tới *{total}* khách hàng...",
        parse_mode="Markdown",
    )

    sent = 0
    failed = 0

    for chat_id_str in users:
        try:
            await ctx.bot.send_message(
                chat_id=int(chat_id_str),
                text=f"📢 *Thông báo từ Cam Ranh Transfer:*\n\n{text}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await update.message.reply_text(
        f"✅ *Gửi hoàn tất!*\n\n"
        f"• Thành công: *{sent}*\n"
        f"• Thất bại: *{failed}* (đã block bot hoặc chat không tồn tại)",
        parse_mode="Markdown",
    )


def build_admin_handlers() -> list:
    return [
        CommandHandler("admin", admin_status),
        CommandHandler("admin_clear", admin_clear),
        CommandHandler("users", admin_users),
        CommandHandler("broadcast", admin_broadcast),
    ]
