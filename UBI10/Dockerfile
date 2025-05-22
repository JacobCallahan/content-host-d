FROM registry.access.redhat.com/ubi10/ubi
LABEL org.opencontainers.image.authors="https://github.com/JacobCallahan"
LABEL broker_compatible="True"

RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host
RUN echo "{\"virt.host_type\": \"Not Applicable\", \"virt.is_guest\": \"False\"}" > /etc/rhsm/facts/custom.facts

# add and process the external resources
ADD resources/* /tmp/
ADD setup_scripts/* /tmp/setup_scripts/

WORKDIR /tmp
RUN chmod +x *.sh setup_scripts/*.sh
RUN for i in `ls setup_scripts/*.sh`; do bash $i; done
WORKDIR /root

RUN sed -i 's/enabled = 1/enabled = 0/g' /etc/yum.repos.d/ubi.repo
RUN dnf clean all

EXPOSE 22

CMD /tmp/startup.sh
