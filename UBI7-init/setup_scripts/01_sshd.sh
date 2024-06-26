yum -y install openssh-server
cat <<EOT >> /etc/ssh/sshd_config.d/99-redhat.conf
PermitRootLogin yes

EOT
systemctl enable sshd

