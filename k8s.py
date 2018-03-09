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
    deployments = api.list_namespaced_deployment(namespace).items
    results = ''
    for d in deployments:
        if d.status.ready_replicas == None:
            ready_replicas = '0'
        else:
            ready_replicas = d.status.ready_replicas
        results += '{}: {} replicas desired, {} ready\n'.format(
            d.metadata.name, d.status.replicas, ready_replicas
        )
    return results

def scale_deployment(name, namespace, replicas):
    api = client.AppsV1Api()
    deployments = api.list_namespaced_deployment(namespace).items
    deployment = [d for d in deployments if d.metadata.name == name]
    if len(deployment) == 0:
        deployment.spec.replicas = replicas
        resp = api.patch_namespaced_deployment_scale(name, namespace, deployment)
        return 'success'
    else:
        return "couldn't find a deployment called " + name

def deploy_image(name, namespace, image):
    api = client.AppsV1Api()
    deployments = api.list_namespaced_deployment(namespace).items
    deployment = [d for d in deployments if d.metadata.name == name]
    if len(deployment) == 0:
        deployment = deployment[0]
        deployment.spec.template.spec.containers[0].image = image
        resp = api.patch_namespaced_deployment(name, namespace, deployment)
        return 'success'
    else:
        return "couldn't find a deployment called " + name

