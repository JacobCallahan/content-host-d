FROM registry.access.redhat.com/rhel7.4
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

# RUN sleep .1 ; printf "%s\n" "dog8code" "dog8code" | passwd
# RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config
# RUN sed -ri 's/#UsePAM no/UsePAM no/g' /etc/ssh/sshd_config
RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
ADD hostname-3.13-3.el7.x86_64.rpm /tmp/
RUN yum -y localinstall /tmp/hostname-3.13-3.el7.x86_64.rpm

EXPOSE 22

CMD /tmp/startup.sh

