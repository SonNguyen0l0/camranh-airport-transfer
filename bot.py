import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler,ContextTypes, CallbackQueryHandler

# Bật ghi log (logging) để theo dõi lỗi hoặc trạng thái của bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_text(lang_code: str, key: str) -> str:
    try:
        # Đường dẫn động tìm đến đúng file vi.json, en.json hoặc ru.json
        file_path = f"languages/{lang_code}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(key, f"[{key}]")  # Trả về chuỗi chữ theo từ khóa (key)
    except Exception:
        return f"[{key}]"  # Nếu lỗi (thiếu file), trả về tạm tên từ khóa



# Hàm xử lý khi người dùng gõ lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 1. Gom lời chào từ 3 ngôn ngữ
    welcome_vi = get_text("vi", "welcome")
    welcome_en = get_text("en", "welcome")
    welcome_ru = get_text("ru", "welcome")
    
    full_message = f"{welcome_vi}\n\n---\n\n{welcome_en}\n\n---\n\n{ru_message}"

    # 2. Tạo hàng nút bấm. Mỗi nút có 'callback_data' để bot biết khách bấm nút nào
    keyboard = [
        [
            InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Gửi tin nhắn chứa menu nút bấm cho khách
    await update.message.reply_text(full_message, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Nhấp nháy báo nhận lệnh từ Telegram để nút bấm không bị treo cát

    # Nếu data là "lang_vi" -> selected_lang sẽ là "vi"
    selected_lang = query.data.replace("lang_", "")
    
    # 💾 QUAN TRỌNG: Lưu mã ngôn ngữ vào bộ nhớ của bot gắn liền với User này
    context.user_data["lang"] = selected_lang

    # Lấy câu thông báo "Đã thiết lập ngôn ngữ thành công..." từ file tương ứng
    response_text = get_text(selected_lang, "lang_selected")

    # Thay đổi (sửa) nội dung tin nhắn cũ thành lời xác nhận ngôn ngữ thành công
    await query.edit_message_text(text=response_text)
    

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
    # Lắng nghe bất kỳ nút bấm nào có callback_data bắt đầu bằng chữ "lang_"
    application.add_handler(CallbackQueryHandler(button_click, pattern="^lang_"))


    # Chạy bot liên tục cho đến khi nhận lệnh dừng (Ctrl+C trên máy tính)
    print("Bot đang chạy... Nhấn Ctrl+C để dừng.")
    application.run_polling()

if __name__ == "__main__":
    main()
