import argparse
from collections import deque
from time import time
import docker


def rm_container(client, containers):
    del_container = containers.popleft()
    client.remove_container(del_container['container'], v=True, force=True)
    print ('Done with container #{0}'.format(del_container['number']))

def host_flood(count, host, key, tag, name, limit, image, criteria, org):
    client = docker.Client(version='1.22')  # docker.from_env()
    num = 1
    containers = deque()
    while num < count or containers:
        if len(containers) < limit and num <= count:  # check if queue is full
            container = client.create_container(
                image='{0}:{1}'.format(image, tag),
                hostname='{0}{1}'.format(name, num),
                detach=False,
                environment={'SATHOST': host, 'AK': key, 'ORG': org},
                volumes='/dev/log:/dev/log:Z'
            )
            containers.append({'container': container, 'number': num})
            client.start(container=container)
            print ('Created: {0}'.format(num))
            num += 1

        logs = client.logs(containers[0]['container']['Id'])
        if criteria == 'reg':
            if 'system has been registered'.encode() in logs:
                rm_container(client, containers)
        elif criteria == 'age':
            if 'Complete!'.encode() in logs:
                rm_container(client, containers)
        else:
            if time() - containers[0].get('delay', time()) >= criteria:
                rm_container(client, containers)
            elif not containers[0].get('delay', False) and 'Complete!'.encode() in logs:
                containers[0]['delay'] = time()
            elif client.inspect_container(containers[0]['container']['Id'])['State']['Status'] != u'running':
                rm_container(client, containers)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tag", type=str,
        help="The image tag you want the container based on. ch-d:<tag>")
    parser.add_argument(
        "host", type=str,
        help="The hostname of the target Satellite.")
    parser.add_argument(
        "name", type=str,
        help="The base hostname to use for the containers.")
    parser.add_argument(
        "key", type=str,
        help="The Activation Key to use for registration.")
    parser.add_argument(
        "count", type=int,
        help="The number of docker content hosts to create.")
    parser.add_argument(
        "--org", type=int, help="The organization to register hosts to "
        "(defaults to 'Default_Organization'.")
    parser.add_argument(
        "--limit", type=int,
        help="The maximum number of simultaneous docker content hosts.")
    parser.add_argument(
        "--image", type=str,
        help="The name of the image to use, defaults to 'ch-d'.")
    parser.add_argument(
        "--exit-criteria", type=str, help="The criteria to kill the host "
        "(registration, katello-agent, <time in seconds>).")
    args = parser.parse_args()

    limit = args.limit if args.limit else 50
    image = args.image if args.image else 'ch-d'
    org = args.org if args.org else 'Default_Organization'
    if args.exit_criteria:
        if 'reg' in args.exit_criteria:
            criteria = 'reg'
        elif 'age' in args.exit_criteria:
            criteria = 'age'
        else:
            try:
                criteria = int(args.exit_criteria)
            except Exception as err:
                criteria = 60
    else:
        criteria = 60

    print ("Starting content host creationi with criteria {}.".format(criteria))
    host_flood(
        args.count, args.host, args.key, args.tag,
        args.name, limit, image, criteria, org
    )
    print ("Finished content host creation.")
