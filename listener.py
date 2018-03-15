import json
import time
from network import check_connection, get_ip
from k8s import get_resources

def slack_startup(sc, channel):
    log_event({'message': 'starting up, checking for internet connection'})
    while True:
        if check_connection('8.8.8.8', 53):
            log_event({'message': 'connected to internet'})
            break
        time.sleep(1)
    sc.rtm_connect(with_team_state=False)
    log_event({'message': 'connected to slack'})
    bot_id = sc.api_call('auth.test')['user_id']
    post_message(sc, "Just waking up...", channel)
    try:
        nodes = get_resources('nodes')
        post_message(sc, nodes, channel)
    except:
        post_message(sc, "Can't talk to k8s...", channel)
    return bot_id

def slack_loop(sc, channel):
    while True:
        args, user = wait_for_command(sc, channel, bot_id)
        if type(args) == list:
            resp, user_must_confirm = handle_command(args)
            if user_must_confirm:
                post_message(sc, "if you're sure you want to {}, mention me again \
and say 'confirm'", channel)
                new_args, new_user = wait_for_command(sc, channel, bot_id, timeout=15)
                if new_args == ['confirm'] and new_user == user:
                    resp = handle_command(args, user_confirmed=True)
            post_message(sc, resp, channel)
        elif type(args) == str:
            resp = handle_file(args)
            handle_file(sc, ch, user, args)
        time.sleep(1)

def post_message(sc, msg, ch, ts=None):
    if msg.startswith('http') and msg.endswith('.jpg'):
        sc.api_call("chat.postMessage", as_user=True, channel=ch,
                    attachments=[{'fallback': 'image', 'image_url': msg}])
    elif ts:
        sc.api_call("chat.postMessage", as_user=True, channel=ch,
                    text=msg, thread_ts=ts)
    else:
        sc.api_call("chat.postMessage", as_user=True, channel=ch, text=msg,)

def wait_for_command(sc, channel, bot_id):
    while True:
        for event in sc.rtm_read():
            args, user = parse_event(event, channel, bot_id)
            if args:
                return args, user
        time.sleep(1)
    return None, None

def confirm_user(sc, channel, user, timeout):
    message = "enter 'confirm' to confirm:"
    post_message(sc, message, channel)
    while timeout > 0:
        for event in sc.rtm_read():
            args, new_user = parse_event(event, channel, bot_id)
            if args == ['confirm'] and new_user == user:
                return True
    return False

def log_event(event):
    event['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S")
    print(json.dumps(event))

def parse_event(event, channel, bot_id):
    mention = '<@{}>'.format(bot_id)
    if event['type'] == 'message' and event['channel'] == channel:
        if not 'subtype' in event and mention in event['text']:
            log_event(event)
            args = event['text'].split()
            args = args[args.index(mention) + 1:]
            return args, event['user']
        elif ('subtype' in event and event['subtype'] == 'file_share' and
              mention in event['file']['initial_comment']['comment']):
            log_event(event)
            return event['file']['url_private'], event['user']
    return None, None

