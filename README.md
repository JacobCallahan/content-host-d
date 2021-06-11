# content-host-d
A Docker-ized Centos Content Host for Red Hat Satellite 6

Current automated tags are: centos5, centos6, centos7, sles11, sles12, opensuse

Manual tags are: rhel6, rhel72, rhel7

Installation
------------
```docker pull jacobcallahan/content-host-d:<tag>```

or specify a directory and build the image manually

```docker build -t ch-d:sles11 SLES11/.```

Usage
-----
```docker run <arguments> jacobcallahan/content-host-d:<tag>```

Accepted Arguments
------------------
-e  (e.g. ```-e "SATHOST=my.hostname.domain.com"```)
 * AK - Name of the Activation Key to use.
 * AUTH - Satellite user name and password. (AUTH=username/password)
 * ENV - Name of the Environment to use.
 * KILL - A flag to terminate the container. If not passed, the container is left alive and goferd running.
 * ORG - The label of the Organization to use.
 * SATHOST (Required) - Host name of the Satellite (FQDN not a URL).
 * LOCAL - IP Address of the Satellite Server when this cannot be retrievied using DNS.

Note
----
If you want to be able to use katello-agent, you must mount your /dev/log to the container at runtime. (i.e. -v /dev/log:/dev/log)

Examples
--------
```docker run -e "SATHOST=my.host.domain.com" jacobcallahan/content-host-d:5```

```docker run -e "SATHOST=my.host.domain.com" -e "LOCAL=192.168.0.10" jacobcallahan/content-host-d:5```

```docker run -e "SATHOST=my.host.domain.com" -e "ENV=Dev" -e "AUTH=username/password" jacobcallahan/content-host-d:6```

```docker run -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" -e "KILL=1" jacobcallahan/content-host-d:7```

```docker run -h DockerCH -v /dev/log:/dev/log -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" jacobcallahan/content-host-d:5```

```for i in {1..10}; do docker run -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" -e "KILL=1" jacobcallahan/content-host-d:6; done;```

```for i in {1..10}; do docker run -d -h Docker$i -e "SATHOST=my.host.domain.com" -e "AK=sat62" jacobcallahan/content-host-d:7; done;```

Flood Script
------------
This repo also contains a flood.py helper script to orchestrate container creation and deletion. You will need python and docker-py (via pip) installed locally.

See ```python flood.py -h``` for usage.

There are two primary modes:
 - Traditional - Create normal content host containers.
 - Virt - Create fake hypervisors on the Satellite, then create guest container hosts.
 
Ansible-playbook run
--------------------
You can also use the available playbooks in `playbooks` folder of this project to setup a container host or run the flood.py script.

Examples
--------
container host setup

```sh
ansible-playbook --inventory=containerhost.example.com, --extra-vars 'WORKSPACE=/home/testlab/workspace/content-host-d CONTAINER_OS=RHEL7' chd-setup.yaml
```
Run flood.py

```sh
ansible-playbook --inventory=containerhost.example.com, --extra-vars 'SATELLITE_HOST=satellite.example.com CONTENT_HOST_PREFIX=testhost ACTIVATION_KEY=rhel7ak NUMBER_OF_HOSTS=3 EXIT_CRITERIA=registration CONTAINER_TAG=rhel7' chd-run.yaml
```
