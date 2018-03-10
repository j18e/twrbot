from kubernetes import client, config

config.load_kube_config()
core = client.CoreV1Api()
apps = client.AppsV1Api()

def get_pods(namespace):
    results = ''
    pod_list = core.list_namespaced_pod(namespace)
    for p in core.list_namespaced_pod(namespace).items:
        results+='{}: {}\n'.format(p.metadata.name, p.status.phase)
    return results

def get_nodes():
    results = ''
    for n in core.list_node().items:
        a = [i.address for i in n.status.addresses if i.type == 'Hostname'][0]
        s = [i.status for i in n.status.conditions if i.type == 'Ready'][0]
        if s == 'True':
            s = 'good to go'
        else:
            s = 'in a bad way'
        results+='{}: {}\n'.format(a, s)
    return results

def get_deployments(namespace):
    deployments = apps.list_namespaced_deployment(namespace).items
    results = ''
    for d in deployments:
        if d.status.ready_replicas == None:
            d.status.ready_replicas = 0
            ready_replicas = '0'
        else:
            ready_replicas = d.status.ready_replicas
        results += '{}: {} replicas desired, {} ready\n'.format(
            d.metadata.name, d.status.replicas, ready_replicas
        )
    return results

def scale_deployment(name, namespace, replicas):
    try:
        deployment = apps.read_namespaced_deployment_scale(name, namespace)
        deployment.spec.replicas = replicas
        resp = apps.patch_namespaced_deployment_scale(name, namespace, deployment)
        return 'success'
    except:
        return 'something went wrong. Did you specify an existing deployment?'

def deploy_image(name, namespace, image):
    try:
        deployment = apps.read_namespaced_deployment(name, namespace)
        deployment.spec.template.spec.containers[0].image = image
        resp = apps.patch_namespaced_deployment(name, namespace, deployment)
        return 'success'
    except:
        return 'something went wrong. Did you specify an existing deployment?'

