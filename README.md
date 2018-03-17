# twrbot
A Python 3 based Slack bot for managing and monitoring Kubernetes clusters

## Overview
The `bot.py` script can be run with either `cmd`, `cli` or `slack` as a single
argument. The first two are for debugging purposes, and faster testing of
functionality. `bot.py` is a script that could be used in any Slack based
chatbot, and only assumes the existence of an `interactions.py` file which
contains a `get_usage` function and `handle_command` function for handling
actual command strings.

## Running
To run the bot from your local machine you'll need to provide `SLACK_TOKEN` and
`SLACK_CHANNEL` in your environment to act as a bot identification and a channel
to listen on. Since twrbot is used to manage/monitor Kubernetes, you'll need to
have a kubeconfig file, probably at `.kube/config`. Python's Kubernetes client
will automatically try to read from this file, which will provide all necessary
access/authentication details for talking to the cluster. For example:
```
SLACK_TOKEN=0923j4gi3q4hgqp08hg9q035u029ht SLACK_CHANNEL=GJI837GI ./bot.py slack
```
The above command will start the bot listening on the given channel, using the
token to identify itself.

### cli loop, single cmd
For testing/development of new functions, you can use the `cli` or `cmd` modes
to run the bot without interfacing with Slack, direct from the command line.
Here are a couple examples:
```
./bot.py cmd where
>> looks like I'm running at 192.168.1.143

./bot.py cmd get nodes
>> minikube - good to go
```

### Docker
The bot has been Dockerized, and is located at `jamesmacfarlane/twrbot`, or
https://hub.docker.com/r/jamesmacfarlane/twrbot/
```
docker run -e SLACK_TOKEN=0923j4gi3q4hgqp08hg9q035u029ht -e SLACK_CHANNEL=GJI837GI jamesmacfarlane/twrbot
```

### Kubernetes
The bot can be run as a single replica Kubernetes deployment; check out
`k8s.yml` for details. It assumes you've created a couple of secrets for both
you Slack info and the contents of the container's `/root/.kube/` directory for
controlling the Kubernetes cluster. The great thing about running it inside of
Kubernetes itself is that if the script errors and crashes for any reason,
Kubernetes will spin up a brand new container to keep serving on Slack.

## Usage
`interactions.py` contains the usage string and thereby all details for sending
requests to the bot, but in summary you can find out about certain resources in
the cluster, scale a deployment to any number of replicas or deploy a new Docker
image to the first container of an existing deployment.
