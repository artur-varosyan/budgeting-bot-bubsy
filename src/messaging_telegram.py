# A proxy for messaging with the user via telegram

from time import sleep
from json import load

from telegram import Update, ForceReply
from telegram.ext import ExtBot, Updater, CommandHandler, MessageHandler, Filters, CallbackContext

message_handler = None

bot_token = None
my_bot = None
chat_id = None
private_bot = False


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    passed = check_permissions(update)
    if not passed:
        return
    else:
        global my_bot
        my_bot = context.bot
        user = update.effective_user
        update.message.reply_markdown_v2(
            fr'Hi {user.mention_markdown_v2()} It is nice to meet you\! Send /help to learn how to talk to me 😄\!',
            reply_markup=ForceReply(selective=True),
        )
        sleep(10)
        my_bot.send_message(chat_id=5079203337, text="Test 2")


def check_permissions(update):
    if private_bot == False:
        return True
    else:
        this_chat_id = update.message.chat_id
        global chat_id
        if this_chat_id == chat_id:
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
        instructions += "- Tell you how much you have spent\n"
        instructions += "- Show you your budget\n"
        instructions += "\nTry sending me these messages:\n"
        instructions += "- I paid £2.10 for a public transport ticket yesterday\n"
        instructions += "- How much did I spend last weekend?\n"
        instructions += "- Show me my budget\n"
        update.message.reply_text(instructions)


def incoming_message(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    passed = check_permissions(update)
    if not passed:
        return
    else:
        replies: [str] = message_handler(update.message.text)
        for reply in replies:
            update.message.reply_text(reply)


def send_message(message):
    if my_bot is not None:
        my_bot.send_message(message)
    return


def init_bot():
    try:
        with open("config.json") as src_file:
            config = load(src_file)
        global bot_token
        global chat_id
        global private_bot
        bot_token = config["token"]
        chat_id = config["chatId"]
        private_bot = config["privateBot"]
    except Exception as e:
        raise RuntimeError("The configuration file 'config.json' is missing or contains errors")


def listen(handler):
    # Start the bot
    init_bot()

    # Create the Updater and pass it your bot's token.
    global bot_token
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # On non command i.e message - call the handler
    global message_handler
    message_handler = handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, incoming_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    listen()
