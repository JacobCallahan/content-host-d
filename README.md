# content-host-d
A Docker-ized Centos Content Host for Red Hat Satellite 6

Installation
------------
```docker pull jacobcallahan/content-host-d```

Usage
-----
```docker run <arguments> jacobcallahan/content-host-d```

Accepted Arguments
------------------
-e  (e.g. ```-e "SATHOST=my.hostname.domain.com"```)
 * AK - Name of the Activation Key to use.
 * AUTH - Satellite username and password.
 * ENV - Name of the Environment to use.
 * ORG - Name of the Organization to use.
 * SATHOST(Required) - Hostname of the Satellite (not url).