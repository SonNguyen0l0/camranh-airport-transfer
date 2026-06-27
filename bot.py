import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CallbackQueryHandler

from handlers.booking import build_conversation_handler, driver_response, book_more_response
from handlers.admin import build_admin_handlers

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Add it to your .env file or Secrets.")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(build_conversation_handler())

    app.add_handler(
        CallbackQueryHandler(driver_response, pattern=r"^driver_(accept|reject|deposit)_\d+$")
    )
    app.add_handler(
        CallbackQueryHandler(book_more_response, pattern=r"^book_more_(yes|no)$")
    )

    for h in build_admin_handlers():
        app.add_handler(h)

    logger.info("🚀 Cam Ranh Airport Transfer bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
