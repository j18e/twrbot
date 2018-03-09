#!/usr/bin/env python3

import time
import json
from os import environ
from random import randint, shuffle
from slackclient import SlackClient
from network import check_connection, get_ip
from k8s import *

sc = SlackClient(environ['SLACK_TOKEN'])
listen_channel = environ['SLACK_CHANNEL']
meme_list = environ['MEMES'].split()
shuffle(meme_list)

usage = """
show - wisdom for your journey
where - ip address of the host I'm running on
get pods - list of pods on k8s cluster
get deployments - list of deployments on k8s cluster
get nodes - list of nodes in k8s cluster
"""

timestamp = lambda : time.strftime("%Y-%m-%dT%H:%M:%S")

def main():
    print(timestamp(), "starting up, checking for internet connection...")
    while True:
        if check_connection('8.8.8.8', 53):
            print(timestamp(), "connected to internet")
            break
        time.sleep(1)
    sc.rtm_connect(with_team_state=False)
    print(timestamp(), "connected to slack")
    bot_id = sc.api_call('auth.test')['user_id']
    post_message("Just waking up...")
    try:
        nodes = get_nodes()
        post_message(nodes)
    except:
        post_message("Derp! Something went wrong talking to the cluster...")
    while True:
        for event in sc.rtm_read():
            command, ts = parse_event(event, bot_id)
            if command:
                handle_command(command, ts)
        time.sleep(1)

def parse_event(event, bot_id):
    mention = '<@{}>'.format(bot_id)
    if event['type'] == 'message' and not 'subtype' in event:
        if mention in event['text'].split() and event['channel'] == listen_channel:
            event['@timestamp'] = timestamp()
            print(json.dumps(event))
            command = event['text'].split()
            mention_idx = command.index(mention)
            return command[mention_idx + 1:], event['ts']
    return None, None

def post_reply(message, ts):
    sc.api_call(
        "chat.postMessage",
        as_user=True,
        channel=listen_channel,
        text=message,
        thread_ts=ts
    )

def post_message(message):
    sc.api_call(
        "chat.postMessage",
        as_user=True,
        channel=listen_channel,
        text=message,
    )

def post_image(url):
    attachment = {
        'fallback': 'meme',
        'image_url': url
    }
    sc.api_call(
        "chat.postMessage",
        as_user=True,
        channel=listen_channel,
        attachments=[attachment]
    )

def handle_command(args, ts):
    response = None
    command = args[0]
    args.pop(0)
    if command == 'show':
        post_image(meme_list[0])
        meme_list.append(meme_list.pop(0))
    elif command == 'where':
        if 'K8S_NODE_IP' in environ:
            location = environ['K8S_NODE_IP']
        else:
            location = get_ip()
        post_message("looks like I'm running at {}".format(location))
    elif command == 'get':
        if args[0] == 'pods':
            response = get_pods('default')
        elif args[0] == 'nodes':
            response = get_nodes()
        elif args[0] == 'deployments':
            response = get_deployments('default')
        else:
            response = "didn't get that. Try again..."
        post_message(response)
    elif command == 'deploy':
        post_message("deploying {} to container {} in deployment {}".format(
            args[1], args[0], args[0])
        )
        deploy_image(args[0], args[0], args[1])
        handle_command(['get', 'deployments'])
    elif command == 'scale':
        post_message("scaling {} to {} replicas...".format(args[0], args[1]))
        scale_deployment(args[0], args[1])
        handle_command(['get', 'pods'])
    elif 'help' in command:
        post_message("Here's what you can ask me:\n" + usage)
    else:
        post_message("Didn't catch that. Here's what you can ask:\n" + usage)

main()
