FROM registry.access.redhat.com/rhel7.0
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

RUN sleep .1 ; printf "%s\n" "dog8code" "dog8code" | passwd
RUN sed -i -e 's/os.path.exists(HOST_CONFIG_DIR)/False/g' /usr/lib64/python2.7/site-packages/rhsm/config.py
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
RUN rpm -Uvh ftp://fr2.rpmfind.net/linux/centos/7.3.1611/os/x86_64/Packages/hostname-3.13-3.el7.x86_64.rpm

EXPOSE 22

CMD /tmp/startup.sh

