from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

# current_dir = os.path.dirname(os.path.abspath(__file__))
# config_file_path = os.path.join(current_dir, "config.ini")
TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
CENSOR = os.environ.get("CENSOR")
STRING = os.environ.get("STRING")

# List of words to censor. Generated by splitting the CENSOR environment variable by commas
censor_list = CENSOR.split(",")


def filter_bot_messages(result):
    filtered_result = []

    for message in result:
        if message.startswith("tldrbot:"):
            continue
        else:
            filtered_result.append(message)

    return filtered_result


def count_words(result):
    count = 0

    for message in result:
        count += len(message.split())

    return count


def censor_result(result, words_to_censor):
    redacted_result = []

    for message in result:
        words = message.split()
        redacted_words = []

        for word in words:
            if word.lower() in words_to_censor:
                redacted_words.append("[REDACTED]")

            # If the word is a substring of a word in the censor list, censor it
            # The substring must be at least 4 string long
            elif any(
                word.lower() in censor_word
                for censor_word in words_to_censor
                if len(word.lower()) >= 4
            ):
                redacted_words.append("[REDACTED]")

            # If the censor word is a substring of the word, censor it
            elif any(
                censor_word.lower() in word.lower() for censor_word in words_to_censor
            ):
                redacted_words.append("[REDACTED]")

            else:
                redacted_words.append(word)

        redacted_string = " ".join(redacted_words)
        redacted_result.append(redacted_string)

    return redacted_result


async def get_chat_history(chat_id, num_messages):
    # Read the Telegram API credentials from a config file.
    # config = configparser.ConfigParser()
    # config.read(config_file_path)

    # # Retrieve the values from the config file.
    # api_id = config["Telegram"]["api_id"]
    # api_hash = config["Telegram"]["api_hash"]
    # chat_id = int(config["Telegram"]["ITUS"])
    # phone = config["Telegram"]["phone_number"]

    # client = TelegramClient(phone, api_id, api_hash)
    client = TelegramClient(StringSession(STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)

    # Start the client.
    await client.start()

    # Get the chat history of the group chat.
    messages = await client.get_messages(chat_id, limit=num_messages)

    # Format according to sender's name and message content.
    result = [
        f"{message.sender.first_name}: {message.message} \n"
        for message in messages
        if not message.action
    ]

    censored_result = censor_result(result, censor_list)

    filtered_result = filter_bot_messages(censored_result)

    # Print out the chat history.
    filtered_result.reverse()

    # print('\n'.join(filtered_result))

    # Print out the number of words in the chat history.
    print(f"Number of words: {count_words(filtered_result)}")

    await client.disconnect()

    return "\n".join(filtered_result)
