from slackclient import SlackClient
from dotenv import load_dotenv
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import re
import signal
from imdb import IMDb

load_dotenv()
slack_token = os.environ.get("SLACK_API_TOKEN")
sc = SlackClient(slack_token)
nickbot_id = None
RTM_READ_DELAY = 1
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

"""Setting up logger"""
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(
    'slackbot.log', mode='a', maxBytes=5*1024*1024, backupCount=2,
    encoding=None, delay=0)
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(threadName)s:%(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

running_flag = True
ia = IMDb()


def receive_signal(signum, stack):
    """Logs Interrupt and Termination signals"""
    logger.warning("Received signal: {}".format(signum))
    global running_flag
    if signum == signal.SIGINT:
        running_flag = False
    if signum == signal.SIGTERM:
        running_flag = False


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API
        to find bot commands.
        If a bot command is found, this function returns a tuple of command
        and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == nickbot_id:
                return message, event["channel"]
            elif sc.api_call('users.info', user=user_id)['user']['is_bot']:
                username = (sc.api_call(
                    'users.info', user=user_id)['user']['real_name'])
                sc.api_call(
                    "chat.postMessage",
                    channel=event['channel'],
                    text="<@{}> exit".format(username)
                )
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning)
        in message text
        and returns the user ID which was mentioned. If there is no
        direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the
    # remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (
        None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    global running_flag
    # Default response is help text for the user
    default_response = ("Not sure what you mean."
                        "Try *{}*, *{}*, or *{}*.".format(
                            42, "top10movies", "worst10movies",
                            "Voight-Kampf"))
    logger.debug("Received command: {} in channel: {}".format(
        command, channel))
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith('42'):
        response = "Life, the Universe, and Everything"
    elif command.startswith('top10movies'):
        top10 = []
        for movie in ia.get_top250_movies()[0:10]:
            top10.append(movie['title'])
        response = "\n".join(top10)
    elif command.startswith('worst10movies'):
        worst10 = []
        for movie in ia.get_bottom100_movies()[-10:]:
            worst10.append(movie['title'])
        response = "\n".join(worst10)
    logger.debug("Reponded with \n{}.".format(response))

    # Sends the response back to the channel
    sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )
    return response


def main():
    signal.signal(signal.SIGINT, receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)
    if sc.rtm_connect(with_team_state=False):
        channels = sc.api_call('conversations.list')['channels']
        for group in sc.api_call('groups.list')['groups']:
            channels.append(group)
        for channel in channels:
            sc.api_call(
                'chat.postMessage',
                channel=channel['id'],
                text="Nick_Bot will slap you with knowledge!"
            )
        start_time = time.time()
        logger.info("Nick_Bot running!")
        # Read bot's user ID by calling Web API method `auth.test`
        global nickbot_id
        nickbot_id = sc.api_call("auth.test")["user_id"]
        print nickbot_id
        while running_flag:
            try:
                command, channel = parse_bot_commands(sc.rtm_read())
                if command:
                    handle_command(command, channel)
                time.sleep(RTM_READ_DELAY)
            except Exception:
                logger.exception(Exception)
                logger.info("Restarting...")
                time.sleep(5)
        logger.info("Shutting Down! Nick_Bot uptime: {} seconds.".format(
            time.time() - start_time))
        for channel in channels:
            sc.api_call(
                'chat.postMessage',
                channel=channel['id'],
                text=("I've seen things you people wouldn't believe. "
                      "Attack ships on fire off the shoulder of Orion. "
                      "I watched C-beams glitter in the dark "
                      "near the Tannhauser Gate. "
                      "All those moments will be lost in time, "
                      "like tears in rain.\n"
                      "Time to die.")
            )
    else:
        logger.exception("Connection Failed!  Exception traceback above.")


if __name__ == '__main__':
    main()
