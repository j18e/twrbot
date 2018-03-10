#!/usr/bin/env python3

import json
import time
import yaml
import requests
from os import environ
from random import shuffle
from slackclient import SlackClient
from network import check_connection, get_ip
from k8s import *

usage = """
show - wisdom for your journey
where - ip address of the host I'm running on
get pods - list of pods on k8s cluster
get deployments - list of deployments on k8s cluster
get nodes - list of nodes in k8s cluster
deploy dhuser/webapp:12.2 my-webapp - install a new Docker image to the first container of an existing deployment
scale my-webapp

Upload a YAML and mention me in the comment, I'll try to install it in the cluster!
"""

timestamp = lambda : time.strftime("%Y-%m-%dT%H:%M:%S")

def main(sc, ch, meme_list=['empty']):
    shuffle(meme_list)
    print(timestamp(), "starting up, checking for internet connection...")
    while True:
        if check_connection('8.8.8.8', 53):
            print(timestamp(), "connected to internet")
            break
        time.sleep(1)
    sc.rtm_connect(with_team_state=False)
    print(timestamp(), "connected to slack")
    bot_id = sc.api_call('auth.test')['user_id']
    post_message(sc, ch, "Just waking up...")
    try:
        nodes = get_nodes()
        post_message(sc, ch, nodes)
    except:
        post_message(sc, ch, "Derp! Something went wrong talking to the cluster...")
    while True:
        for event in sc.rtm_read():
            event_type, content = parse_event(ch, event, bot_id)
            if event_type == 'message':
                handle_command(sc, ch, content)
            elif event_type == 'file':
                handle_file(sc, ch, content)
        time.sleep(1)

def parse_event(ch, event, bot_id):
    mention = '<@{}>'.format(bot_id)
    if event['type'] == 'message':
        if not 'subtype' in event:
            if mention in event['text'].split() and event['channel'] == ch:
                event['@timestamp'] = timestamp()
                print(json.dumps(event))
                command = event['text'].split()
                mention_idx = command.index(mention)
                return 'message', command[mention_idx + 1:]
        elif event['subtype'] == 'file_share':
            if mention in event['file']['initial_comment']['comment']:
                event['@timestamp'] = timestamp()
                print(json.dumps(event))
                return 'file', event['file']['url_private']
    return None, None

def post_reply(sc, ch, message, ts):
    sc.api_call("chat.postMessage", as_user=True, channel=ch,
                text=message, thread_ts=ts)

def post_message(sc, ch, message):
    sc.api_call("chat.postMessage", as_user=True, channel=ch,
                text=message,)

def post_image(sc, ch, url):
    attachment = {'fallback': 'meme', 'image_url': url}
    sc.api_call("chat.postMessage", as_user=True, channel=ch,
                attachments=[attachment])

def sort_manifests(doc_list):
    manifests = {'service': [], 'deployment': []}
    response = ''
    for d in doc_list:
        manifests[d['kind']].append(d)
    for kind, manifest_list in manifests.items():
        if len(manifest_list) > 0:
            response+='{} {}s\n'.format(len(manifest_list), kind)
    return manifests

def handle_command(sc, ch, args):
    response = None
    command = args[0]
    args.pop(0)
    if command == 'show':
        post_image(sc, ch, meme_list[0])
        meme_list.append(meme_list.pop(0))
    elif command == 'where':
        if 'K8S_NODE_IP' in environ:
            location = environ['K8S_NODE_IP']
        else:
            location = get_ip()
        post_message(sc, ch, "looks like I'm running at {}".format(location))
    elif command == 'get':
        if args[0] == 'pods':
            response = get_pods('default')
        elif args[0] == 'nodes':
            response = get_nodes()
        elif args[0] == 'deployments':
            response = get_deployments('default')
        else:
            response = "Didn't catch that. Here's what you can ask:\n" + usage
        post_message(sc, ch, response)
    elif command == 'deploy':
        post_message(sc, ch, "installing image {} to deployment {}".format(
            args[0], args[1]))
        post_message(sc, ch, update_image(args[1], 'default', args[0]))
    elif command == 'scale':
        post_message(sc, ch, "scaling {} to {} replicas...".format(args[0], args[1]))
        post_message(sc, ch, scale_deployment(args[0], 'default', args[1]))
    elif 'help' in command:
        post_message(sc, ch, "Here's what you can ask me:\n" + usage)
    else:
        post_message(sc, ch, "Didn't catch that. Here's what you can ask:\n" + usage)

def handle_file(sc, ch, url):
    auth = {'Authorization': 'Bearer {}'.format(sc.token)}
    resp = requests.get(url, headers=auth)
    try:
        doc_list = list(yaml.load_all(resp.text))
        manifests = sort_manifests(doc_list)
    except:
        response = "that didn't work. You need to send me only yaml formated \
Kubernetes manifests of kind deployment or service"
        return
    counts = {k: len(l) for k, l in manifests.items() if len(l) > 0}
    response = yaml.dump(counts, default_flow_style=False)
    response = 'counts of manifests you want to deploy:\n' + response
    post_message(sc, ch, response)

main(SlackClient(environ['SLACK_TOKEN']), environ['SLACK_CHANNEL'],
     meme_list=environ['MEMES'].split())
