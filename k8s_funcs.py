from kubernetes import client, config

config.load_kube_config()
core = client.CoreV1Api()
apps = client.AppsV1Api()

def get_resources(kind, namespace='default'):
    results = ''
    if kind.startswith('pod'):
        for p in core.list_namespaced_pod(namespace).items:
            results += '{}: {} on {}\n'.format(
                p.metadata.name,
                p.status.phase,
                p.spec.node_name
            )
    elif kind.startswith('node'):
        for n in core.list_node().items:
            a = [i.address for i in n.status.addresses if i.type == 'Hostname'][0]
            s = [i.status for i in n.status.conditions if i.type == 'Ready'][0]
            if s == 'True':
                s = 'good to go'
            else:
                s = 'in a bad way'
            results+='{}: {}\n'.format(a, s)
    elif kind.startswith('deploy'):
        for d in apps.list_namespaced_deployment(namespace).items:
            if d.status.ready_replicas == None:
                d.status.ready_replicas = 0
                ready_replicas = '0'
            else:
                ready_replicas = d.status.ready_replicas
            results += '{}: {} replicas desired, {} ready\n'.format(
                d.metadata.name, d.status.replicas, ready_replicas
            )
    else:
        return None
    return results

def delete_resource(kind, name, namespace='default'):
    if kind.startswith('deploy'):
        if name == 'twrbot':
            return 'I cannot self terminate'
        result = apps.delete_namespaced_deployment(name, namespace, {})
        result = result['status']
    elif kind.startswith('pod'):
        result = core.delete_namespaced_pod(name, namespace, {})
        result = get_resources('pod')
    return result

def scale_deployment(name, replicas, namespace='default'):
    try:
        replicas = int(replicas)
        deployment = apps.read_namespaced_deployment_scale(name, namespace)
        deployment.spec.replicas = replicas
        resp = apps.patch_namespaced_deployment_scale(name, namespace, deployment)
        return 'success'
    except:
        return 'something went wrong. Did you specify an existing deployment?'

def deploy_image(name, image, namespace='default'):
    try:
        deployment = apps.read_namespaced_deployment(name, namespace)
        deployment.spec.template.spec.containers[0].image = image
        resp = apps.patch_namespaced_deployment(name, namespace, deployment)
        return 'success'
    except:
        return 'something went wrong. Did you specify an existing deployment?'

