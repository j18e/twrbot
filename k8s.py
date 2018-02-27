from kubernetes import client, config
from subprocess import Popen

config.load_kube_config()
v1 = client.CoreV1Api()

def get_pods(namespace):
    pod_list = v1.list_namespaced_pod(namespace)
    return ["{}\t{}\t{}".format(pod.metadata.name,
                         pod.status.phase,
                         pod.status.pod_ip)
            for pod in pod_list.items]

def get_nodes():
    results = []
    for node in v1.list_node().items:
        address = [a for a in node.status.addresses if a.type == 'Hostname'][0].address
        state = [c for c in node.status.conditions if c.type == 'Ready'][0].status
        results.append("{} ready: {}".format(address, state))
    return results

def get_deployments(namespace):
    results = []
    for d in api.list_namespaced_deployment(namespace).items:
        results.append("{}: {} replicas ready".format(d.metadata.name, d.status.ready_replicas))
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
