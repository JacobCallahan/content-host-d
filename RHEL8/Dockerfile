FROM registry.access.redhat.com/ubi8
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host
RUN echo "{\"virt.host_type\": \"Not Applicable\", \"virt.is_guest\": \"False\"}" > /etc/rhsm/facts/custom.facts
RUN echo -e "\nexport LC_ALL=C\nexport LANG=C\n" >> .bashrc
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
ADD hostname-3.20-6.el8.x86_64.rpm /tmp/
RUN yum -y localinstall /tmp/hostname-3.20-6.el8.x86_64.rpm

EXPOSE 22

CMD /tmp/startup.sh
