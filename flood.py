import argparse, json, os, sys, time, uuid
from collections import deque
import docker

def merge_dicts(dict1, dict2):
    res = dict1.copy()
    res.update(dict2)
    return res

def gen_json(hypervisors, guests):
    virtwho = {}
    all_guest_list = []
    for i in range(hypervisors):
        guest_list = []
        for c in range(guests):
            cur_id = str(uuid.uuid4())
            guest_list.append({
                "guestId": cur_id,
                "state": 1,
                "attributes": {
                    "active": 1,
                    "virtWhoType": "esx"
                }
            })
            all_guest_list.append(cur_id)
        virtwho[str(uuid.uuid4()).replace("-", ".")] = guest_list
    return (virtwho, all_guest_list)

def rm_container(client, containers):
    del_container = containers[0]
    client.remove_container(del_container['container'], v=True, force=True)
    del containers[0]
    print ('Done with {0}'.format(del_container['name']))

def host_flood(count, tag, name, env_vars, limit, image, criteria):
    client = docker.Client(version='1.22')  # docker.from_env()
    num = 1
    containers = deque()
    while num < count or containers:
        if len(containers) < limit and num <= count:  # check if queue is full
            container = client.create_container(
                image='{0}:{1}'.format(image, tag),
                hostname='{0}{1}'.format(name, num),
                detach=False,
                environment=env_vars,
                volumes='/dev/log:/dev/log:Z'
            )
            containers.append({'container': container, 'name': num})
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
            elif 'no enabled repos'.encode() in logs:
                rm_container(client, containers)
            elif 'No package katello-agent available'.encode() in logs:
                rm_container(client, containers)
        else:
            if 'no enabled repos'.encode() in logs:
                rm_container(client, containers)
            elif 'No package katello-agent available'.encode() in logs:
                rm_container(client, containers)
            elif time.time() - containers[0].get('delay', time.time()) >= criteria:
                rm_container(client, containers)
            elif not containers[0].get('delay', False) and 'Complete!'.encode() in logs:
                containers[0]['delay'] = time.time()
            elif client.inspect_container(containers[0]['container']['Id'])['State']['Status'] != u'running':
                rm_container(client, containers)

def virt_flood(tag, limit, image, name, env_vars, hypervisors, guests):
    virt_data, guest_list = gen_json(hypervisors, guests)
    with open('/tmp/temp.json', 'w') as f:
        json.dump(virt_data, f)
    client = docker.Client(version='1.22')
    temphost = 'meeseeks-{}'.format(str(uuid.uuid4()))
    print ("Submitting virt-who report. Note: this will create a host: '{}'.".format(temphost))
    client.pull('jacobcallahan/genvirt')
    container = client.create_container(
        image='jacobcallahan/genvirt',
        hostname=temphost,
        detach=False,
        environment=env_vars,
        volumes='/tmp/temp.json',
        host_config=client.create_host_config(binds={
            '/tmp/temp.json': {'bind': '/tmp/temp.json', 'mode': 'ro'}
        })
    )
    client.start(container=container)
    while 'Done!'.encode() not in client.logs(container):
        time.sleep(2)
    client.remove_container(container, v=True, force=True)
    os.remove('/tmp/temp.json')
    if sys.version_info.major < 3:
        _ = raw_input("Pausing for you to attach subscriptions to the new hypervisors.")
    else:
   	    _ = input("Pausing for you to attach subscriptions to the new hypervisors.")

    print("Starting guest creation.")
    active_hosts = []
    while guest_list or active_hosts:
        if guest_list and len(active_hosts) < limit:
            guest = guest_list.pop(0)
            hostname = '{}{}'.format(name, guest.split('-')[4])
            container = client.create_container(
                image='{0}:{1}'.format(image, tag),
                hostname=hostname,
                detach=False,
                environment=merge_dicts(env_vars, {'UUID': guest})
            )
            active_hosts.append({'container': container, 'name': hostname})
            client.start(container=container)
            print ('Created Guest: {}. {} left in queue.'.format(hostname, len(guest_list)))

        logs = client.logs(active_hosts[0]['container']['Id'])
        # We'll wait for 30 seconds after attempting to auto-attach
        if 'no enabled repos'.encode() in logs:
            rm_container(client, active_hosts)
        elif 'No package katello-agent available'.encode() in logs:
            rm_container(client, active_hosts)
        elif time.time() - active_hosts[0].get('delay', time.time()) >= 30:
            rm_container(client, active_hosts)
        elif not active_hosts[0].get('delay', False) and 'auto-attach'.encode() in logs:
            active_hosts[0]['delay'] = time.time()
        elif client.inspect_container(active_hosts[0]['container']['Id'])['State']['Status'] != u'running':
            rm_container(client, active_hosts)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--image", type=str, default="ch-d",
        help="The name of the image to use, defaults to 'ch-d'.")
    parser.add_argument(
        "-t", "--tag", type=str, default="rhel7",
        help="The image tag you want the container based on. ch-d:<tag>")
    parser.add_argument(
        "-s", "--satellite", type=str, required=True,
        help="The hostname of the target Satellite.")
    parser.add_argument(
        "-n", "--name", type=str, default="flood",
        help="The base hostname to use for the containers.")
    parser.add_argument(
        "-k", "--key", type=str,
        help="The Activation Key to use for registration.")
    parser.add_argument(
        "-o", "--organization", type=str, help="The organization to "
        " register hosts to(defaults to 'Default_Organization'.")
    parser.add_argument(
        "-e", "--environment", type=str, help="The location to register hosts to "
        "(defaults to 'Default_Location'.")
    parser.add_argument(
        "-a", "--auth", type=str, help="Specify a different username and password "
        "in the format: username/password (defaults to 'admin/changeme'.")
    parser.add_argument(
        "-c", "--count", type=int, default=10,
        help="The number of docker content hosts to create.")
    parser.add_argument(
        "--hypervisors", type=int,
        help="The number of hypervisors to create."
        " This is only to be used with the 'guest' tag")
    parser.add_argument(
        "--guests", type=int,
        help="The number of guests per hypervisor to create."
        " This is only to be used with the 'guest' tag")
    parser.add_argument(
        "--limit", type=int, default=1000,
        help="The maximum number of simultaneous docker content hosts.")
    parser.add_argument(
        "--exit-criteria", type=str, help="The criteria to kill the host "
        "(registration, katello-agent, <time in seconds>).")
    args = parser.parse_args()

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

    # gather our environmental variables to pass to the containers
    env_vars = {'SATHOST': args.satellite}
    if args.key:
        env_vars['AK'] = args.key
    if args.organization:
        env_vars['ORG'] = args.organization
    if args.environment:
        env_vars['ENV'] = args.environment
    if args.auth:
        env_vars['AUTH'] = args.auth

    if args.hypervisors:
        print ("Starting population of hypervisor(s) and guest(s)")
        tag = 'guest' if not args.tag else args.tag
        guests = 5 if not args.guests else args.guests
        virt_flood(tag, args.limit, args.image, args.name,
                   env_vars, args.hypervisors, guests)
    else:
        print ("Starting content host creation with criteria {}.".format(criteria))
        host_flood(args.count, args.tag, args.name, env_vars,
                   args.limit, args.image, criteria)
    print ("Finished content host creation.")
