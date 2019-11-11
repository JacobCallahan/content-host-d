#!/usr/bin/python
import argparse, json, os, sys, time, uuid
from collections import deque
import click
import docker
import logging


def merge_dicts(dict1, dict2):
    res = dict1.copy()
    res.update(dict2)
    return res


def gen_json(hypervisors, guests):
    virtwho = {}
    all_guest_list = []
    for _ in range(hypervisors):
        guest_list = []
        for __ in range(guests):
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


def compile_guests(json_data):
    """Recurse through the json and pick out all the guestIds"""
    compiled = []
    if isinstance(json_data, list):
        # we won't see guests in a list, so we'll go deeper
        for child in json_data:
            result = compile_guests(child)
            if result:
                compiled.extend(result)
        return compiled
    if isinstance(json_data, dict):
        # we may find the guestId in this dict
        if json_data.get("guestId"):
            compiled.append("guestId")
            return compiled
        else:
            # we're not on the correct level. find nested elements and recurse
            for child in json_data.values():
                result = compile_guests(child)
                if result:
                    compiled.extend(result)
            return compiled


def get_guests(f_path):
    """get a list of all unique guests from the provided virt-who json file"""
    json_data = None
    with open(f_path) as df:
        json_data = json.load(df)
    guest_list = list(set(compile_guests(json_data)))
    return guest_list


def rm_container(client, containers, reason="Success"):
    del_container = containers[0]
    with open("container.log", "a") as log:
        log.write(
            "***********************************{0}****************************\n".format(
                del_container["name"]
            )
        )
        log.write(client.logs(del_container["container"]["Id"]))
    client.remove_container(del_container["container"], v=True, force=True)
    del containers[0]
    logging.info("Done with {0}: {1}".format(del_container["name"], reason))


def package_envars(**kwargs):
    """gather our environmental variables to pass to the containers"""
    env_vars = {"SATHOST": kwargs.get("satellite")}
    if kwargs.get("key"):
        env_vars["AK"] = kwargs.get("key")
    if kwargs.get("organization"):
        env_vars["ORG"] = kwargs.get("organization")
    if kwargs.get("environment"):
        env_vars["ENV"] = kwargs.get("environment")
    if kwargs.get("auth"):
        env_vars["AUTH"] = kwargs.get("auth")
    return env_vars


def cli_defaults(func):
    func = click.option(
        "-i",
        "--image",
        type=str,
        default="ch-d",
        help="The name of the image to use, defaults to 'ch-d'.",
        prompt=True,
    )(func)
    func = click.option(
        "-t",
        "--tag",
        type=str,
        default="rhel7",
        help="The image tag you want the container based on. ch-d:<tag>",
        prompt=True,
    )(func)
    func = click.option(
        "-m", "--network-mode", help="Container network mode to use.", type=str
    )
    func = click.option(
        "-n",
        "--name",
        type=str,
        default="flood",
        help="The base hostname to use for the containers.",
    )(func)
    func = click.option(
        "-s",
        "--satellite",
        help="The hostname of the target Satellite.",
        type=str,
        prompt=True,
    )(func)
    func = click.option(
        "-k", "--key", help="The Activation Key to use for registration.", type=str
    )(func)
    func = click.option(
        "-o",
        "--organization",
        type=str,
        help="The organization to register hosts to(defaults to 'Default_Organization'.",
    )(func)
    func = click.option(
        "-e",
        "--environment",
        type=str,
        help="The environment to register hosts to (defaults to 'Default_Location'.",
    )(func)
    func = click.option(
        "-a",
        "--auth",
        type=str,
        help="Specify a different username and password in the format: username/password (defaults to 'admin/changeme'.",
    )(func)
    func = click.option(
        "-c",
        "--count",
        type=int,
        default=10,
        help="The number of docker content hosts to create.",
    )(func)
    func = click.option(
        "--limit",
        type=int,
        default=1000,
        help="The maximum number of simultaneous docker content hosts.",
    )(func)
    func = click.option(
        "--exit-criteria",
        type=str,
        default="60",
        help="The criteria to kill the host "
        "(registration, katello-agent, <time in seconds>).",
    )(func)
    func = click.option(
        "--rhsm-log-dir",
        type=str,
        help="A directory path to store "
        "rhsm.log files. If no directory exists, it will be created.",
    )(func)
    return func


@cli_defaults
def host_flood(**kwargs):
    client = docker.Client(version="1.22")  # docker.from_env()
    num = 1
    containers = deque()
    env_vars = package_envars(**kwargs)
    # create our base volume bind
    binds = {"/dev/log": {"bind": "/dev/log", "mode": "rw"}}
    # allow for local storage of rhsm logs
    rhsm_log_dir = kwargs.get("rhsm_log_dir")
    if rhsm_log_dir:
        rhsm_log_dir = "" if rhsm_log_dir == "." else rhsm_log_dir
        if not os.path.isabs(rhsm_log_dir):
            rhsm_log_dir = os.path.abspath(rhsm_log_dir)
        if not os.path.isdir(rhsm_log_dir):
            os.makedirs(rhsm_log_dir)

    logging.info(
        "Starting content host creation with criteria {}.".format(
            kwargs.get("criteria")
        )
    )
    while num < kwargs.get("count") or containers:
        if len(containers) < kwargs.get("limit") and num <= kwargs.get(
            "count"
        ):  # check if queue is full
            local_file = None
            if rhsm_log_dir:
                # create our log bind
                local_file = "{}/{}{}.log".format(rhsm_log_dir, kwargs.get("name"), num)
                with open(local_file, "w"):
                    pass
                binds[local_file] = {"bind": "/var/log/rhsm/rhsm.log", "mode": "rw"}
            hostname = "{0}{1}".format(kwargs.get("name"), num)
            container = client.create_container(
                image="{0}:{1}".format(kwargs.get("image"), kwargs.get("tag")),
                hostname=hostname,
                detach=False,
                environment=env_vars,
                host_config=client.create_host_config(binds=binds),
            )
            # destroy the bind for this host, for the next one
            if binds.get(local_file or None):
                del binds[local_file]
            containers.append({"container": container, "name": hostname})
            client.start(container=container, network_mode=kwargs.get("network_mode"))
            logging.info("Created: {0}".format(hostname))
            num += 1

        logs = client.logs(containers[0]["container"]["Id"])

        if "reg" in kwargs.get("criteria"):
            if "system has been registered".encode() in logs:
                rm_container(client, containers)
            elif "no enabled repos".encode() in logs:
                rm_container(
                    client,
                    containers,
                    "No repos enabled. Check registration/subscription status.",
                )
        elif "age" in kwargs.get("criteria"):
            if "Complete!".encode() in logs:
                rm_container(client, containers)
            elif "no enabled repos".encode() in logs:
                rm_container(
                    client,
                    containers,
                    "No repos enabled. Check registration/subscription status.",
                )
            elif "No package katello-agent available".encode() in logs:
                rm_container(client, containers, "katello-agent not found.")
        else:
            criteria = int(kwargs.get("criteria"))
            if "No package katello-agent available".encode() in logs:
                rm_container(client, containers, "katello-agent not found.")
            elif "no enabled repos".encode() in logs:
                rm_container(
                    client,
                    containers,
                    "No repos enabled. Check registration/subscription status.",
                )
            elif time.time() - containers[0].get("delay", time.time()) >= criteria:
                rm_container(client, containers)
            elif not containers[0].get("delay", False) and "Complete!".encode() in logs:
                containers[0]["delay"] = time.time()
            elif (
                client.inspect_container(containers[0]["container"]["Id"])["State"][
                    "Status"
                ]
                != u"running"
            ):
                rm_container(client, containers)
    logging.info("Finished content host creation.")


@click.command()
@cli_defaults
@click.option(
    "--hypervisors",
    type=int,
    default=5,
    help="The number of hypervisors to create."
    " This is only to be used with the 'guests' tag",
)
@click.option(
    "--guests",
    type=int,
    default=5,
    help="The number of guests per hypervisor to create."
    " This is only to be used with the 'hypervisors' tag",
)
@click.option(
    "-r",
    "--virt-report",
    help="The path to a virt-who report file to be passed in.",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--preserve", help="Use to keep the generated virt-who json file.", is_flag=True
)
def virt_flood(**kwargs):
    if kwargs.get("virt_report"):
        guest_list = get_guests(f_path=kwargs.get("virt_report"))
    else:
        json_volume = "virt-report.json"
        virt_data, guest_list = gen_json(
            kwargs.get("hypervisors"), kwargs.get("guests")
        )
        with open("virt-report.json", "w") as f:
            json.dump(virt_data, f)
    client = docker.Client(version="1.22")
    env_vars = package_envars(**kwargs)
    temphost = "meeseeks-{}".format(str(uuid.uuid4()))
    logging.info(
        "Submitting virt-who report. Note: this will create a host: '{}'.".format(
            temphost
        )
    )
    client.pull("jacobcallahan/genvirt")
    container = client.create_container(
        image="jacobcallahan/genvirt",
        hostname=temphost,
        detach=False,
        environment=env_vars,
        volumes=json_volume,
        host_config=client.create_host_config(
            binds={json_volume: {"bind": "/tmp/temp.json", "mode": "ro"}}
        ),
    )
    client.start(container=container, network_mode=kwargs.get("network_mode"))
    while "Done!".encode() not in client.logs(container):
        time.sleep(2)
    client.remove_container(container, v=True, force=True)
    if not kwargs.get("virt_report") and not kwargs.get("preserve"):
        os.remove("virt-report.json")
    if sys.version_info.major < 3:
        _ = raw_input("Pausing for you to attach subscriptions to the new hypervisors.")
    else:
        _ = input("Pausing for you to attach subscriptions to the new hypervisors.")

    logging.info("Starting guest creation.")
    active_hosts = []
    while guest_list or active_hosts:
        if guest_list and len(active_hosts) < kwargs.get("limit"):
            guest = guest_list.pop(0)
            hostname = "{}{}".format(kwargs.get("name"), guest.split("-")[4])
            container = client.create_container(
                image="{0}:{1}".format(kwargs.get("image"), kwargs.get("tag", "guest")),
                hostname=hostname,
                detach=False,
                environment=merge_dicts(kwargs.get("env_vars"), {"UUID": guest}),
            )
            active_hosts.append({"container": container, "name": hostname})
            client.start(container=container, network_mode=kwargs.get("network_mode"))
            logging.info(
                "Created Guest: {}. {} left in queue.".format(hostname, len(guest_list))
            )

        logs = client.logs(active_hosts[0]["container"]["Id"])
        # We'll wait for 30 seconds after attempting to auto-attach
        if "no enabled repos".encode() in logs:
            rm_container(client, active_hosts)
        elif "No package katello-agent available".encode() in logs:
            rm_container(client, active_hosts)
        elif time.time() - active_hosts[0].get("delay", time.time()) >= 30:
            rm_container(client, active_hosts)
        elif not active_hosts[0].get("delay", False) and "auto-attach".encode() in logs:
            active_hosts[0]["delay"] = time.time()
        elif (
            client.inspect_container(active_hosts[0]["container"]["Id"])["State"][
                "Status"
            ]
            != u"running"
        ):
            rm_container(client, active_hosts)
    logging.info("Finished content host creation.")


if __name__ == "__main__":
    logging.basicConfig(
        filename="flood.log",
        format="[%(levelname)s %(asctime)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S",
        level=logging.INFO,
    )
