#!/usr/bin/env python3

import os
import time
import re
from slackclient import SlackClient
from network import check_connection
from k8s import *

sc = SlackClient(os.environ['SLACK_TOKEN'])
listen_channel = os.environ['SLACK_CHANNEL']
node_ip = os.environ['K8S_NODE_IP']

def main():
    print(ts(), "starting up, checking for internet connection...")
    while True:
        if check_connection('8.8.8.8', 53):
            print(ts(), "connected to internet")
            break
        time.sleep(1)
    if sc.rtm_connect(with_team_state=False):
        print(ts(), "connected to slack")
        bot_id = sc.api_call('auth.test')['user_id']
        post_message("Just waking up...")
        try:
            nodes = get_nodes()
            post_message(nodes)
        except:
            port_message("Derp! Something went wrong talking to the cluster...")
        while True:
            command, channel = parse_bot_commands(sc.rtm_read(), bot_id)
            if (command and channel == listen_channel):
                handle_command(command)
            time.sleep(1)
    else:
        print(ts(), 'Connection failed. Exception traceback printed above.')

def post_message(message):
    sc.api_call("chat.postMessage", as_user=True, channel=listen_channel, text=message)

ts = lambda : time.strftime("%Y-%m-%dT%H:%M:%S")

def parse_bot_commands(slack_events, bot_id):
    for event in slack_events:
        if event['type'] == 'message' and not 'subtype' in event:
            user_id, message = parse_direct_mention(event['text'])
            if user_id == bot_id:
                event['@timestamp'] = ts()
                print(event)
                return message.split(), event['channel']
    return None, None

def parse_direct_mention(text):
    regex = '^<@(|[WU].+?)>(.*)'
    matches = re.search(regex, text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command):
    response = None
    if command[0] == 'random':
        post_message("we're gonna party :fiesta_parrot:")
    elif command[0] == 'where':
        post_message("looks like I'm running at {}".format(node_ip))
    elif command[0] == 'get':
        if command[1] == 'pods':
            response = get_pods('default')
        elif command[1] == 'nodes':
            response = get_nodes()
        elif command[1] == 'deployments':
            response = get_deployments('default')
        else:
            response = ["didn't get that. Try again..."]
        post_message('returning {} {}...'.format(len(response), command[1]))
        for l in response:
            post_message(l)
    elif command[0] == 'deploy':
        usage = "deploy containername repository:tag"
        post_message("deploying {} to container {} in deployment {}".format(
            command[2], command[1], command[1])
        )
        deploy_image(command[1], command[1], command[2])
        handle_command(['get', 'deployments'])
    elif command[0] == 'scale':
        usage = "scale deploymentname number"
        post_message("scaling {} to {} replicas...".format(command[1], command[2]))
        scale_deployment(command[1], command[2])
        handle_command(['get', 'pods'])
    else:
        post_message("Ask again. My responses are limited...")

main()
