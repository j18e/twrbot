from kubernetes import client, config
from subprocess import Popen

config.load_kube_config()
v1 = client.CoreV1Api()

def get_pods(namespace):
    results = ''
    pod_list = v1.list_namespaced_pod(namespace)
    for p in v1.list_namespaced_pod(namespace).items:
        results+='{}: {}\n'.format(p.metadata.name, p.status.phase)
    return results

def get_nodes():
    results = ''
    for n in v1.list_node().items:
        a = [i.address for i in n.status.addresses if i.type == 'Hostname'][0]
        s = [i.status for i in n.status.conditions if i.type == 'Ready'][0]
        if s == 'True':
            s = 'good to go'
        else:
            s = 'in a bad way'
        results+='{}: {}\n'.format(a, s)
    return results

def get_deployments(namespace):
    api = client.AppsV1Api()
    results = ''
    for d in api.list_namespaced_deployment(namespace).items:
        results+='{}: {} healthy replicas\n'.format(d.metadata.name, d.status.ready_replicas)
    return results

def scale_deployment(deployment, replicas):
    shell_args = [
        'kubectl',
        'scale',
        '--replicas={}'.format(replicas),
        'deployments/{}'.format(deployment),
    ]
    r = Popen(shell_args)
    r.communicate()

def deploy_image(deployment, container, image):
    shell_args = [
        'kubectl',
        'set',
        'image',
        'deployments/{}'.format(deployment),
        '{}={}'.format(container, image),
    ]
    r = Popen(shell_args)
    r.communicate()
