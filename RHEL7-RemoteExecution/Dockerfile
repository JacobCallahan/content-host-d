FROM registry.access.redhat.com/rhel7.7
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

RUN yum install -y openssh-server
RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host
RUN echo "{\"virt.host_type\": \"Not Applicable\", \"virt.is_guest\": \"False\"}" > /etc/rhsm/facts/custom.facts
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
ADD hostname-3.13-3.el7.x86_64.rpm /tmp/
RUN yum -y localinstall /tmp/hostname-3.13-3.el7.x86_64.rpm
RUN /usr/bin/ssh-keygen -A

EXPOSE 22

CMD /tmp/startup.sh
