from slackclient import SlackClient
from os import environ
from time import sleep

sc = SlackClient(environ['SLACK_TOKEN'])
channel = environ['SLACK_CHANNEL']

def main(sc, channel):
    bot_id = slack_startup(sc, channel)
    while True:
        for event in sc.rtm_read():
            args = parse_event(event, channel, bot_id)
            if args:
                resp = handle_command(args)
                post_message(sc, channel, resp)
        sleep(1)

def post_message(sc, ch, message):
    sc.api_call("chat.postMessage",
                as_user=True,
                channel=ch,
                text=message)

def slack_startup(sc, channel):
    sc.rtm_connect(with_team_state=False)
    bot_id = sc.api_call('auth.test')['user_id']
    print('connected to slack')
    post_message(sc, channel, "just waking up...")
    return bot_id

def parse_event(event, channel, bot_id):
    mention = '<@{}>'.format(bot_id)
    if (event['type'] == 'message' and
        'subtype' not in event and
        event['channel'] == channel
        and mention in event['text']):
        print(event)
        args = event['text'].split()
        args = args[args.index(mention) + 1:]
        return args
    return None

def handle_command(args):
    if args[0] == 'help':
        resp = 'here is help'
    return resp

main(sc, channel)
