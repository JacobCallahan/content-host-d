#!/usr/bin/python
import argparse, json, os, sys, time, uuid
from collections import deque
import logging

try:
    from lib.podman import PodmanContainer as ContainerImpl
except ImportError:
    from lib.docker import DockerContainer as ContainerImpl


class Container(ContainerImpl):
    def __init__(self, *, image, tag, hostname, env_vars, criteria=None, network_mode, binds=[], command=None):
        self.image = image
        self.tag = tag
        self.hostname = hostname
        self.env_vars = env_vars
        self.network_mode = network_mode
        self.binds = binds
        self.command = command
        self.expiry = 0
        self.criteria = criteria

        super().__init__()
        self._ctr = self.get_container()

    def _parse_binds(self):
        return list(map(lambda b: '{}:{}:{}'.format(b['host_path'], b['container_path'], b['mode']), self.binds))

    def get_result(self):
        result = None
        if self.criteria == 'reg':
            if self.search_logs('system has been registered'):
                result = 'Registration complete'
            elif self.search_logs('no enabled repos'):
                result = 'No repos enabled. Check registration/subscription status.'
        elif self.criteria == 'age':
            if self.search_logs('Complete!'):
                result = 'Success'
            if self.search_logs('no enabled repos'):
                result = 'No repos enabled. Check registration/subscription status.'
            elif self.search_logs('No package katello-agent available'):
                result = 'katello-agent not found.'
        else:
            if self.search_logs('No package katello-agent available'):
                result = 'katello-agent not found.'
            elif self.search_logs('no enabled repos'):
                result = 'No repos enabled. Check registration/subscription status.'
            elif 0 < self.expiry < time.time():
                result = 'Time elapsed'
            elif self.expiry == 0 and self.search_logs('system has been registered'):
                self.expiry = time.time() + self.criteria
            elif not self.running():
                result = 'Container not running'
        return result


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
            guest_list.append(
                {
                    "guestId": cur_id,
                    "state": 1,
                    "attributes": {"active": 1, "virtWhoType": "esx"},
                }
            )
            all_guest_list.append(cur_id)
        virtwho[str(uuid.uuid4()).replace("-", ".")] = guest_list
    return (virtwho, all_guest_list)


def rm_container(container, reason):
    with open("container.log", "a") as log:
        log.write(
            "***********************************{0}****************************\n".format(
                container.hostname
            )
        )
        for clog in container.get_logs():
            log.write(clog)
    container.destroy()
    logging.info('Done with {0}: {1}'.format(container.hostname, reason))


def host_flood(count, tag, name, env_vars, limit, image, network_mode, criteria, rhsm_log_dir):
    num = 0
    containers = deque()
    # allow for local storage of rhsm logs
    if rhsm_log_dir:
        rhsm_log_dir = '' if rhsm_log_dir == '.' else rhsm_log_dir
        if not os.path.isabs(rhsm_log_dir):
            rhsm_log_dir = os.path.abspath(rhsm_log_dir)
        if not os.path.isdir(rhsm_log_dir):
            os.makedirs(rhsm_log_dir)

    while num < count or containers:
        if len(containers) < limit and num < count:  # check if queue is full
            # send container logs to host's journal
            binds = [{'container_path': '/dev/log', 'host_path': '/dev/log', 'mode': 'rw'}]
            if rhsm_log_dir:
                local_file = '{}/{}{}.log'.format(rhsm_log_dir, name, num)
                with open(local_file, 'w'):
                    pass
                binds.append({'container_path': '/var/log/rhsm/rhsm.log', 'host_path': local_file, 'mode': 'rw'})

            hostname = '{0}{1}'.format(name, num)
            container = Container(
                    image=image,
                    tag=tag,
                    hostname=hostname,
                    env_vars=env_vars,
                    criteria=criteria,
                    network_mode=network_mode,
                    binds=binds
                )
            containers.append(container)
            container.start()
            logging.info('Created: {0}'.format(hostname))
            num += 1

        container = containers.popleft()
        result = container.get_result()
        if result:
            rm_container(container, result)
        else:
            containers.append(container)


def virt_flood(tag, limit, image, name, criteria, env_vars, network_mode, hypervisors, guests):
    virt_data, guest_list = gen_json(hypervisors, guests)
    with open('/tmp/temp.json', 'w') as f:
        json.dump(virt_data, f)
    temphost = 'meeseeks-{}'.format(str(uuid.uuid4()))
    logging.info(
        "Submitting virt-who report. Note: this will create a host: '{}'.".format(
            temphost
        )
    )
    container = Container(
        image='jacobcallahan/genvirt',
        tag='latest',
        hostname=temphost,
        env_vars=env_vars,
        binds=[{'container_path': '/tmp/temp.json', 'host_path': '/tmp/temp.json', 'mode': 'ro'}],
        network_mode=network_mode,
        command='/tmp/startup.sh',
    )
    container.start()
    while not container.search_logs('Done!'):
        time.sleep(2)
    container.destroy()
    os.remove('/tmp/temp.json')
    if sys.version_info.major < 3:
        _ = raw_input("Pausing for you to attach subscriptions to the new hypervisors.")
    else:
        _ = input("Pausing for you to attach subscriptions to the new hypervisors.")

    logging.info("Starting guest creation.")
    active_hosts = []
    while guest_list or active_hosts:
        if guest_list and len(active_hosts) < limit:
            guest = guest_list.pop(0)
            hostname = '{}{}'.format(name, guest.split('-')[4])
            container = Container(
                image=image,
                tag=tag,
                criteria=criteria,
                network_mode=network_mode,
                hostname=hostname,
                env_vars=merge_dicts(env_vars, {'UUID': guest}),
            )
            active_hosts.append(container)
            container.start()
            logging.info(
                'Created Guest: {}. {} left in queue.'.format(hostname, len(guest_list))
            )

        container = active_hosts.popleft()
        result = container.get_result()
        if result:
            rm_container(container, result)
        else:
            active_hosts.append(container)


if __name__ == '__main__':
    logging.basicConfig(
        filename='flood.log',
        format='[%(levelname)s %(asctime)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S',
        level=logging.INFO,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--image",
        type=str,
        default="ch-d",
        help="The name of the image to use, defaults to 'ch-d'.",
    )
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        default="rhel7",
        help="The image tag you want the container based on. ch-d:<tag>",
    )
    parser.add_argument(
        "-m",
        "--network-mode",
        type=str,
        default=None,
        help="Container network mode to use.",
    )
    parser.add_argument(
        "-s",
        "--satellite",
        type=str,
        required=True,
        help="The hostname of the target Satellite.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="flood",
        help="The base hostname to use for the containers.",
    )
    parser.add_argument(
        "-k", "--key", type=str, help="The Activation Key to use for registration."
    )
    parser.add_argument(
        "-o",
        "--organization",
        type=str,
        help="The organization to "
        " register hosts to(defaults to 'Default_Organization'.",
    )
    parser.add_argument(
        "-e",
        "--environment",
        type=str,
        help="The location to register hosts to " "(defaults to 'Default_Location'.",
    )
    parser.add_argument(
        "-a",
        "--auth",
        type=str,
        help="Specify a different username and password "
        "in the format: username/password (defaults to 'admin/changeme'.",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=10,
        help="The number of content hosts to create.",
    )
    parser.add_argument(
        "--hypervisors",
        type=int,
        help="The number of hypervisors to create."
        " This is only to be used with the 'guests' tag",
    )
    parser.add_argument(
        "--guests",
        type=int,
        help="The number of guests per hypervisor to create."
        " This is only to be used with the 'hypervisors' tag",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="The maximum number of simultaneous content hosts.",
    )
    parser.add_argument(
        "--exit-criteria",
        type=str,
        help="The criteria to kill the host "
        "(registration, katello-agent, <time in seconds>).",
    )
    parser.add_argument(
        "--rhsm-log-dir",
        type=str,
        help="A directory path to store "
        "rhsm.log files. If no directory exists, it will be created.",
    )
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
        logging.info("Starting population of hypervisor(s) and guest(s)")
        tag = 'guest' if not args.tag else args.tag
        guests = 5 if not args.guests else args.guests
        virt_flood(
            tag, args.limit, args.image, args.name, criteria, env_vars, args.network_mode, args.hypervisors, guests
        )
    else:
        logging.info(
            "Starting content host creation with criteria {}.".format(criteria)
        )
        host_flood(
            args.count,
            args.tag,
            args.name,
            env_vars,
            args.limit,
            args.image,
            args.network_mode,
            criteria,
            args.rhsm_log_dir,
        )
    logging.info("Finished content host creation.")
