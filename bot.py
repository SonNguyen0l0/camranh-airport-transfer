import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Bật ghi log (logging) để theo dõi lỗi hoặc trạng thái của bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hàm xử lý khi người dùng gõ lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Chào {user.first_name}! 👋 Tôi là bot AI của bạn. Hãy gõ /hoi để tôi tư vấn nhé!")

# Hàm xử lý khi người dùng gõ lệnh /hoi (Đây chính là 'bộ não' của bot)
async def brain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bạn có thể thay đổi đoạn text phản hồi bên dưới theo ý muốn
    reply_message = "🧠 Đây là phản hồi từ bộ não bot của tôi! Bạn có muốn hỏi thêm gì không?"
    await update.message.reply_text(reply_message)

def main() -> None:
    # Lấy TOKEN từ biến môi trường (Render sẽ tự động cung cấp bảo mật cái này cho bạn)
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Khởi tạo ứng dụng bot
    application = Application.builder().token(TOKEN).build()

    # Đăng ký các lệnh (command) để bot nhận diện
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hoi", brain))

    # Chạy bot liên tục cho đến khi nhận lệnh dừng (Ctrl+C trên máy tính)
    print("Bot đang chạy... Nhấn Ctrl+C để dừng.")
    application.run_polling()

if __name__ == "__main__":
    main()
