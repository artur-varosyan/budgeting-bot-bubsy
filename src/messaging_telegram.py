# A proxy for messaging with the user via telegram

import logging

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
message_handler = None


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    passed = check_permissions(update)
    if not passed:
        return
    else:
        user = update.effective_user
        update.message.reply_markdown_v2(
            fr'Hi {user.mention_markdown_v2()} It is nice to meet you\! Send /help to learn how to talk to me 😄\!',
            reply_markup=ForceReply(selective=True),
        )


def check_permissions(update):
    chat_id = update.message.chat_id
    if chat_id == 5079203337:
        return True
    else:
        update.message.reply_text("Sorry you are not authorised to use this!")
        return False


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    passed = check_permissions(update)
    if not passed:
        return
    else:
        instructions = "Here are some of the thins I can do ✨\n"
        instructions += "- Record an expense\n"
        instructions += "- Tell you how much you spent\n"
        instructions += "- Show you your budget\n"
        instructions += "\nTry sending me these messages:\n"
        instructions += "- I paid £2.10 for a public transport ticket yesterday\n"
        instructions += "- How much did I spend last weekend?\n"
        instructions += "- Show me my budget\n"
        update.message.reply_text(instructions)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    passed = check_permissions(update)
    if not passed:
        return
    else:
        reply = message_handler(update.message.text)
        update.message.reply_text(reply)


def listen(handler):
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5066423723:AAGBJddhgS8T6URtA6jRjMJjvLabKikJeak")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    global message_handler
    message_handler = handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    listen()
