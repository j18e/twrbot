#!/usr/bin/env python3

import yaml
import requests
from os import environ
from sys import argv
from random import shuffle
from k8s import *
from slackclient import SlackClient
from listener import slack_loop, slack_startup, post_message, wait_for_command
from network import check_connection, get_ip

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

def handle_command(args, user_confirmed=False):
    result = None
    user_confirm = False
    command = args[0]
    args.pop(0)
    if command == 'show':
        result = meme_list[0]
        meme_list.append(meme_list.pop(0))
    elif command == 'where':
        result = "looks like I'm running at {}".format(get_ip())
    elif command == 'get':
        try:
            result = get_resources(args[0])
        except:
            result = None
    elif command == 'delete':
        if not user_confirmed:
            result = "you're asking to delete {}\n".format(args)
            user_confirm = True
        else:
            delete_resource(args)
    elif command == 'deploy':
        try:
            result = 'attempting to install image {} to deployment {}'.format(
                args[0], args[1])
            result += update_image(args[1], args[0])
        except:
            result = None
    elif command == 'scale':
        try:
            result = 'attempting to scale {} to {} replicas\n'.format(
                args[0], args[1])
            result += scale_deployment(args[0], args[1])
        except:
            result = None
    elif 'help' in command:
        result = "Here's what you can ask me:\n" + usage
    # endif
    if result:
        return result, user_confirm
    else:
        return "Didn't catch that. You can say 'help'.", user_confirm

def handle_file(url, user_confirmed=False):
    auth = {'Authorization': 'Bearer {}'.format(sc.token)}
    resp = requests.get(url, headers=auth)
    try:
        doc_list = list(yaml.load_all(resp.text))
        manifests = sort_manifests(doc_list)
    except:
        return "that didn't work. You need to send me only yaml formated \
Kubernetes manifests of kind deployment or service"
    counts = {k: len(l) for k, l in manifests.items() if len(l) > 0}
    return 'manifests to apply:\n' + dump_yaml(counts)

dump_yaml = lambda d: yaml.dump(d, default_flow_style=False)

def sort_manifests(doc_list):
    manifests = {'service': [], 'deployment': []}
    response = ''
    for d in doc_list:
        manifests[d['kind']].append(d)
    for kind, manifest_list in manifests.items():
        if len(manifest_list) > 0:
            response+='{} {}s\n'.format(len(manifest_list), kind)
    return manifests

def slack_loop():
    channel = environ['SLACK_CHANNEL']
    sc = SlackClient(environ['SLACK_TOKEN'])
    bot_id = slack_startup(sc, channel)
    while True:
        args, user = wait_for_command(sc, channel, bot_id)
        if type(args) is list:
            resp, user_must_confirm = handle_command(args)
            if user_must_confirm:
                post_message(sc, resp, channel)
                if confirm_user(sc, channel, user, 15):
                    resp, _ = handle_command(args, user_confirmed=True)
                else:
                    resp = "timed out, doing nothing..."
            post_message(sc, resp, channel)
        elif type(args) is str:
            handle_file()

def cli_loop():
    print(usage.rstrip(), '\n--------')
    while True:
        args = input('enter command: ').split()
        print()
        resp, user_must_confirm = handle_command(args)
        if user_must_confirm:
            if input("enter 'confirm' if sure: ") == 'confirm':
                resp, _ = handle_command(args, user_confirmed=True)
            else:
                resp = "doing nothing..."
        print(resp.rstrip(), '\n--------')

if __name__ == '__main__':
    meme_list = ['no wisdom to speak of...']
    if 'MEMES' in environ:
        meme_list = environ['MEMES'].split()
        shuffle(meme_list)
    if len(argv) < 2:
        print('must specify slack or cli as argument')
        exit()
    if argv[1] == 'slack':
        slack_loop()
    elif argv[1] == 'cli':
        cli_loop()
    else:
        print('must specify slack or cli as argument')
        exit()

