# content-host-d
A Docker-ized Centos Content Host for Red Hat Satellite 6
Current tags are: 5, 6, 7, latest

Installation
------------
```docker pull jacobcallahan/content-host-d:<tag>```

Usage
-----
```docker run <arguments> jacobcallahan/content-host-d:<tag>```

Accepted Arguments
------------------
-e  (e.g. ```-e "SATHOST=my.hostname.domain.com"```)
 * AK - Name of the Activation Key to use.
 * AUTH - Satellite username and password. (AUTH=username/password)
 * ENV - Name of the Environment to use.
 * KILL - If this is not passed, then the container will be kept alive and goferd running.
 * ORG - Name of the Organization to use.
 * SATHOST(Required) - Hostname of the Satellite (not url).

Note
----
If you want to be able to use katello-agent, you must mount your /dev/log to the container at runtime. (i.e. -v /dev/log:/dev/log)

Examples
--------
```docker run -e "SATHOST=my.host.domain.com" jacobcallahan/content-host-d:5```

```docker run -e "SATHOST=my.host.domain.com" -e "ENV=Dev" -e "AUTH=username/password" jacobcallahan/content-host-d:6```

```docker run -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" -e "KILL=1" jacobcallahan/content-host-d:7```

```docker run -h DockerCH -v /dev/log:/dev/log -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" jacobcallahan/content-host-d:5```

```for i in {1..10}; do docker run -d -e "SATHOST=my.host.domain.com" -e "AK=sat62" -e "KILL=1" jacobcallahan/content-host-d:6; done;```

```for i in {1..10}; do docker run -d -h Docker$i -e "SATHOST=my.host.domain.com" -e "AK=sat62" jacobcallahan/content-host-d:7; done;```