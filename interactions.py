import re
import socket
import paramiko
from os import environ
from random import shuffle
from k8s_funcs import get_resources, delete_resource, scale_deployment, deploy_image

def get_usage():
    return """
show - wisdom for your journey
where - ip address of the host I'm running on
get pods - list of pods on k8s cluster
get deployments - list of deployments on k8s cluster
get nodes - list of nodes in k8s cluster
deploy dhuser/webapp:12.2 my-webapp - install a new Docker image to the first container of an existing deployment
scale my-webapp
    """.rstrip()

def handle_command(args, confirmed=False):
    result = None
    must_confirm = False
    command = args[0]
    args = args[1:]
    if command == 'show':
        result = 'no wisdom to speak of...'
        if 'MEMES' in environ:
            result = environ['MEMES'].split()
            shuffle(result)
            result = result[0]
    elif command == 'where':
        result = "looks like I'm running at {}".format(get_ip())
    elif command == 'get':
        try:
            result = get_resources(args[0])
        except:
            result = None
    elif command == 'delete':
        if confirmed:
            result = delete_resource(args[0], args[1])
        else:
            result = "you're asking to delete {} {}".format(args[0], args[1])
            must_confirm = True
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
        result = "Here's what you can ask me:\n" + get_usage()
    # endif
    if result:
        return result, must_confirm
    else:
        return "Didn't catch that. You can say 'help'.", must_confirm

# not currently in use
def handle_file(url, confirmed=False):
    auth = {'Authorization': 'Bearer {}'.format(sc.token)}
    resp = requests.get(url, headers=auth)
    try:
        doc_list = list(yaml.load_all(resp.text))
        manifests = sort_manifests(doc_list)
    except:
        return "that didn't work. You need to send me only yaml formated \
Kubernetes manifests of kind deployment or service"
    counts = {k: len(l) for k, l in manifests.items() if len(l) > 0}
    return 'apply manifests:\n' + yaml.dump(counts, default_flow_style=False)

def sort_manifests(doc_list):
    manifests = {'service': [], 'deployment': []}
    response = ''
    for d in doc_list:
        manifests[d['kind']].append(d)
    for kind, manifest_list in manifests.items():
        if len(manifest_list) > 0:
            response+='{} {}s\n'.format(len(manifest_list), kind)
    return manifests

def get_ip():
    if 'GATEWAY_ADDR' in environ:
        command = "ifconfig %s" % (environ['GATEWAY_EXTERNAL_INT'])
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(environ['GATEWAY_ADDR'],
                       username=environ['GATEWAY_USER'],
                       password=environ['GATEWAY_PASSWORD'])
        stdin, stdout, stderr = client.exec_command(command)
        for line in stdout:
            if 'inet addr:' in line:
                result = line.split()[1]
        result = result.split(':')[1]
        client.close()
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        result = s.getsockname()[0]
    return result

