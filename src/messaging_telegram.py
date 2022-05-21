from messaging_abstract import CommunicationMethod

from typing import Callable
from time import sleep
from json import load

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# A proxy for messaging with the user via telegram
class TelegramMessaging(CommunicationMethod):

    # Initialise attributes when instantiated
    def __init__(self):
        self.message_handler = None
        self.bot_token = None
        self.my_bot = None
        self.chat_id = None
        self.private_bot = False

    # Handle start command
    def start_command(self, update: Update, context: CallbackContext) -> None:
        print(f"> Received Command: /start")
        passed = self.check_permissions(update)
        if not passed:
            return
        else:
            self.my_bot = context.bot
            user = update.effective_user
            update.message.reply_markdown_v2(
                fr'Hi {user.mention_markdown_v2()} It is nice to meet you\! Send /help to learn how to talk to me 😄\!',
                reply_markup=ForceReply(selective=True),
            )

    # Check if the message author is authorised
    def check_permissions(self, update) -> bool:
        if not self.private_bot:
            return True
        else:
            this_chat_id = update.message.chat_id
            if this_chat_id == self.chat_id:
                return True
            else:
                update.message.reply_text("Sorry you are not authorised to use this!")
                return False

    # Handle help command
    def help_command(self, update: Update, context: CallbackContext) -> None:
        print(f"> Received Command: /help")
        passed = self.check_permissions(update)
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

    # Analyse the incoming message and pass it to handler
    def incoming_message(self, update: Update, context: CallbackContext) -> None:
        passed = self.check_permissions(update)
        if not passed:
            return
        else:
            replies: [str] = self.message_handler(update.message.text)
            for reply in replies:
                update.message.reply_text(reply)

    # Send a message to the user
    def send_message(self, message: str):
        if self.my_bot is not None:
            self.my_bot.send_message(message)
        return

    # Read in the configuration file and set user settings
    def init_bot(self):
        try:
            with open("telegram_config.json") as src_file:
                config = load(src_file)
            self.bot_token = config["token"]
            self.chat_id = config["chatId"]
            self.private_bot = config["privateBot"]
        except Exception:
            raise RuntimeError("The configuration file 'telegram_config.json' is missing or contains errors")

    def listen(self, handler: Callable[[str], str]):
        # Start the bot
        self.init_bot()

        # Create the Updater and pass it your bot's token.
        updater = Updater(self.bot_token)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", self.start_command))
        dispatcher.add_handler(CommandHandler("help", self.help_command))

        # On non command i.e message - call the handler
        self.message_handler = handler
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.incoming_message))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C
        updater.idle()

