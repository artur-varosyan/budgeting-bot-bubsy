from messaging_abstract import CommunicationMethod

from typing import Callable
from json import load

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# A proxy for messaging with the user via telegram
class TelegramMessaging(CommunicationMethod):

    # Initialise attributes when instantiated
    def __init__(self):
        self.message_handler = None
        self.photo_handler = None
        self.bot_token = None
        self.my_bot = None
        self.chat_id = None
        self.private_bot = False

    # Read in the configuration file and set user settings
    def initialise(self) -> None:
        try:
            with open("telegram_config.json") as src_file:
                config = load(src_file)
            self.bot_token = config["token"]
            self.chat_id = config["chatId"]
            self.private_bot = config["privateBot"]
        except Exception:
            raise RuntimeError("The configuration file 'telegram_config.json' is missing or contains errors")

    # Check if the message author is authorised
    def check_permissions(self, update: Update) -> bool:
        if not self.private_bot:
            return True
        else:
            this_chat_id = update.message.chat_id
            if this_chat_id == self.chat_id:
                return True
            else:
                print(f"!> Unauthorised message: '{update.message.text}'"
                      f"\n   Sender: {update.effective_user.full_name} UserID: {update.effective_user.id}")
                print("<! Permission Denied")
                update.message.reply_text("Sorry you are not authorised to use this!")
                return False

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

    # Handle help command
    def help_command(self, update: Update, context: CallbackContext) -> None:
        print(f"> Received Command: /help")
        passed = self.check_permissions(update)
        if not passed:
            return
        else:
            self.my_bot = context.bot
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

        self.my_bot = context.bot
        replies: [str] = self.message_handler(update.message.text)
        for reply in replies:
            update.message.reply_text(reply)

    # Analyse the incoming photo message and pass it to handler
    def incoming_photo(self, update: Update, context: CallbackContext) -> None:
        passed = self.check_permissions(update)
        if not passed:
            return

        # Last photo has the highest quality
        photo = update.message.photo[-1]
        file = context.bot.getFile(photo.file_id)

        # Download the photo and store as a bytearray in memory
        photo_bytes = file.download_as_bytearray()

        replies = self.photo_handler(photo_bytes)
        for reply in replies:
            update.message.reply_text(reply)

    # Send a message to the user
    def send_message(self, message: str) -> None:
        if self.my_bot is not None:
            self.my_bot.send_message(chat_id=self.chat_id, text=message)

    def echo_user_details(self, update: Update, context: CallbackContext) -> None:
        print(f"> Message: '{update.message.text}'"
              f"\n   Sender: {update.effective_user.full_name} UserID: {update.effective_user.id}")

    # Listen for incoming messages from all users and print their details
    # Used for configuration
    def identify_users(self) -> None:
        self.private_bot = False

        # Create the Updater and pass it your bot's token.
        updater = Updater(self.bot_token)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo_user_details))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C
        updater.idle()

    def listen(self, text_handler: Callable[[str], str], photo_handler: Callable[[bytearray], str]):
        # Create the Updater and pass it your bot's token.
        updater = Updater(self.bot_token)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", self.start_command))
        dispatcher.add_handler(CommandHandler("help", self.help_command))

        # On non command i.e message - call the handler
        self.message_handler = text_handler
        self.photo_handler = photo_handler
        dispatcher.add_handler(MessageHandler(Filters.photo, self.incoming_photo))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.incoming_message))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C
        updater.idle()
