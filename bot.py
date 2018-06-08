#!/usr/bin/env python3

import json
import time
from sys import argv
from os import environ
from slackclient import SlackClient
from interactions import get_usage, handle_command

def single_cmd(args):
    resp, must_confirm = handle_command(args)
    if must_confirm:
        print(resp)
        if input("enter 'confirm' if sure: ") == 'confirm':
            resp, _ = handle_command(args, confirmed=True)
        else:
            resp = "doing nothing..."
    print(resp)

def cli_loop():
    print(get_usage(), '\n--------')
    while True:
        args = input('enter command: ').split()
        print()
        resp, must_confirm = handle_command(args)
        if must_confirm:
            if input("enter 'confirm' if sure: ") == 'confirm':
                resp, _ = handle_command(args, confirmed=True)
            else:
                resp = "doing nothing..."
        print(resp, '\n--------')

def slack_loop():
    channel = environ['SLACK_CHANNEL']
    sc = SlackClient(environ['SLACK_TOKEN'])
    bot_id = slack_startup(sc, channel)
    while True:
        args, user = await_command(sc, channel, bot_id)
        resp, must_confirm = handle_command(args)
        if must_confirm:
            post_message(sc, channel, resp)
            if await_confirmation(sc, channel, bot_id, user, 15):
                resp, _ = handle_command(args, confirmed=True)
            else:
                resp = "timed out, doing nothing..."
        post_message(sc, channel, resp)

def slack_startup(sc, channel):
    sc.rtm_connect(with_team_state=False)
    log_event('connected to slack')
    bot_id = sc.api_call('auth.test')['user_id']
    post_message(sc, channel, "just waking up...")
    return bot_id

def post_message(sc, ch, msg, ts=None):
    if type(msg) is list:
        if len(msg) < 20:
            msg = '\n'.join(msg)
        elif len(msg) < 200:
            msg = ' '.join(msg)
        else:
            msg = 'too many results to post here...'
    elif type(msg) is int:
        msg = str(msg)
    if msg.startswith('http') and msg.endswith('.jpg'):
        sc.api_call("chat.postMessage", as_user=True, channel=ch,
                    attachments=[{'fallback': 'image', 'image_url': msg}])
    elif ts:
        sc.api_call("chat.postMessage", as_user=True, channel=ch,
                    text=msg, thread_ts=ts)
    else:
        sc.api_call("chat.postMessage", as_user=True, channel=ch, text=msg,)
    log_event({'type': 'post', 'message': msg})

def await_command(sc, channel, bot_id):
    while True:
        try:
            for event in sc.rtm_read():
                args, user = parse_event(event, channel, bot_id)
                if args:
                    return args, user
        except WebSocketConnectionClosedException:
            sc.rtm_connect()
        time.sleep(1)
    return None, None

def await_confirmation(sc, channel, bot_id, user, timeout):
    post_message(sc, channel, "enter 'confirm' to confirm:")
    while timeout > 0:
        for event in sc.rtm_read():
            if (event['type'] == 'message' and not 'subtype' in event and
                event['channel'] == channel and event['text'] == 'confirm' and
                event['user'] == user):
                log_event(event)
                return True
        timeout -= 1
        time.sleep(1)
    log_event('timed out awaiting confirmation')
    return False

def log_event(event):
    if type(event) is str:
        result = {'message': event, 'type': 'informational'}
    elif type(event) is dict:
        result = event
    else:
        print(event)
        return
    result['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S")
    print(json.dumps(result))

def parse_event(event, channel, bot_id):
    mention = '<@{}>'.format(bot_id)
    if (event['type'] == 'message' and not 'subtype' in event and
        event['channel'] == channel and mention in event['text']):
            log_event(event)
            args = event['text'].split()
            args = args[args.index(mention) + 1:]
            return args, event['user']
    return None, None

if __name__ == '__main__':
    if len(argv) < 2:
        print('must specify slack, cli or cmd as argument')
        exit()
    elif argv[1] == 'slack':
        slack_loop()
    elif argv[1] == 'cli':
        cli_loop()
    elif argv[1] == 'cmd':
        single_cmd(argv[2:])

