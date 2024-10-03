#!/home/tux/bin/player/env/bin/python

import os
import logging
import subprocess

# telegram related tools
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Replace 'TOKEN' and 'CHAT_ID' with your bot's token and chat id in the .env file
TOKEN = os.getenv("TOKEN")
# make sure the chat id is linked to your message only, replace your token below and send a message to the bot
# to find it, use your browser --> https://api.telegram.org/bot<TOKEN>/getUpdates
CHAT_ID = int(os.getenv("CHAT_ID"))

# Define your playlists
playlists = {
    'welcome': './playlist/welcome.m3u',
    'background': './playlist/background.m3u',
    'seeyou': './playlist/seeyou.m3u',
}

def create_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Welcome", callback_data="welcome"),
            InlineKeyboardButton("Background", callback_data="background"),
            InlineKeyboardButton("Goodbye", callback_data="seeyou"),
        ],
        [InlineKeyboardButton("Stop Music", callback_data="stop")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    reply_markup = create_keyboard()
    if update.message.chat.id != CHAT_ID:
        await update.message.reply_text("Sorry, I'm unable to respond to you. Please contact the author.")
        return

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


def send_command(command):
    global MUSIC_PROCESS
    try:
        MUSIC_PROCESS.stdin.write(command + "\n")
        MUSIC_PROCESS.stdin.flush()
    except (AttributeError, BrokenPipeError):
        pass  # None object has no ... this happens when it was not previously created


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    global MUSIC_PROCESS

    await query.answer()
    if query.data in ['pause', 'stop']:
        await query.edit_message_text(text=f"Performing: {query.data}")
        send_command(query.data)

    else:
        await query.edit_message_text(text=f"Playing playlist: {query.data}")
        send_command('stop')
        # Command to play the playlist using VLC or any other player
        MUSIC_PROCESS = subprocess.Popen(
            ['flatpak', 'run', '--command=cvlc', 'org.videolan.VLC', '--play-and-exit', '--intf', 'rc', playlists[query.data]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Normal package:
        # os.system(f'cvlc --play-and-exit "{playlists[playlist_name]}" &')  # Adjust command as needed

        # Flatpak:
        # cmd = f'flatpak run --command=cvlc org.videolan.VLC --play-and-exit "{playlists[playlist_name]}" &'

        # MacOS:
        # cmd = /Applications/VLC.app/Contents/MacOS/cvlc

    # always show the keyboard again for ease of usage
    reply_markup = create_keyboard()
    await query.message.reply_text("Please choose:", reply_markup=reply_markup)


if __name__ == '__main__':
    global MUSIC_PROCESS
    MUSIC_PROCESS = None

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()
