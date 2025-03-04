#!/bin/bash
mkdir host_tools
# shellcheck disable=SC2164
cd host_tools
for pkg in "gofer-2.7.6-1.el7.noarch.rpm" \
    "katello-client-repos-3.5.1-1.el7.noarch.rpm" \
    "katello-client-repos-latest.rpm" \
    "katello-host-tools-3.1.0-1.el7.noarch.rpm" \
    "katello-host-tools-fact-plugin-3.1.0-1.el7.noarch.rpm" \
    "pulp-rpm-handlers-2.13.4-1.el7.noarch.rpm" \
    "python-amqp-1.4.9-1.el7.noarch.rpm" \
    "python-gofer-2.7.6-1.el7.noarch.rpm" \
    "python-gofer-amqp-2.7.6-1.el7.noarch.rpm" \
    "python-gofer-proton-2.7.6-1.el7.noarch.rpm" \
    "python-gofer-qpid-2.7.6-1.el7.noarch.rpm" \
    "python-isodate-0.5.0-4.pulp.el7.noarch.rpm" \
    "python-pulp-agent-lib-2.13.4-1.el7.noarch.rpm" \
    "python-pulp-common-2.13.4-1.el7.noarch.rpm" \
    "python-pulp-rpm-common-2.13.4-1.el7.noarch.rpm" \
    "python-saslwrapper-0.22-5.el7.x86_64.rpm" \
    "katello-agent-3.1.0-1.el7.noarch.rpm" \
    "saslwrapper-0.22-5.el7.x86_64.rpm"; \
do wget https://fedorapeople.org/groups/katello/releases/yum/3.5/client/el7/x86_64/$pkg; done
rpm -Uvh * --nodeps