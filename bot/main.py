import logging
from uuid import uuid4
from datetime import datetime
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    filters,
)
from utils.history import get_chat_history
from utils.gpt_summarizer import get_summary
import os

# Env variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "5000"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a group chat summarizer bot.",
    )


async def help_command(update: Update, context):
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def summarize_command(update: Update, context):
    """Summarize the conversation."""
    logger.info("Summarizing conversation...")
    chat_id = update.effective_chat.id

    num_messages = 50  # default value
    if context.args:
        try:
            num_messages = int(context.args[0])
            if num_messages < 1:
                num_messages = 50
            if num_messages >= 400:
                await update.message.reply_text(
                    "Too many messages. Please provide a number less than 400."
                )
                return
        except ValueError:
            await update.message.reply_text(
                "Invalid number of messages. Please provide a valid number."
            )
            return

    try:
        result = await get_chat_history(chat_id, num_messages)
    except Exception as e:
        logger.error(e)
        await context.bot.send_message(
            chat_id=chat_id,
            text="An error occurred. Please try reducing the number of messages.",
        )
        return

    caller_info = update.effective_user
    logger.info(f"Conversation summarized by {caller_info.name} ({caller_info.id})")

    prefix = f"_Conversation summarized by {caller_info.name} for the last {num_messages} messages:_\n\n"
    postfix = ""

    summary = prefix + get_summary(result) + postfix
    summary = summary.replace(".", "\.")
    summary = summary.replace("-", "\-")
    summary = summary.replace("(", "\(")
    summary = summary.replace(")", "\)")

    await context.bot.send_message(
        chat_id=chat_id,
        text=summary,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
    )


async def inline_query(update: Update, context):
    """Handle inline queries."""
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Summarize Conversation",
            input_message_content=InputTextMessageContent(f"/tldr"),
            description="Summarize the conversation in the group chat",
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Start",
            input_message_content=InputTextMessageContent(f"/start"),
            description="Start the bot",
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Help",
            input_message_content=InputTextMessageContent(f"/help"),
            description="Display help information",
        ),
    ]
    await update.inline_query.answer(results)


def main():
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tldr", summarize_command))

    # Register inline query handler
    application.add_handler(InlineQueryHandler(inline_query))

    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(PORT),
            url_path=BOT_TOKEN,
            webhook_url=os.getenv("WEBHOOK_URL") + BOT_TOKEN,
        )
        logger.info("Application running via webhook: ")
    else:
        application.run_polling()
        logger.info("Application running via polling: ")


if __name__ == "__main__":
    main()
