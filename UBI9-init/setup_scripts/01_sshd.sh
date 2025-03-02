dnf -y install openssh-server
mkdir -p /etc/ssh/sshd_config.d
cat <<EOT >> /etc/ssh/sshd_config.d/99-redhat.conf
PermitRootLogin yes

EOT
systemctl enable sshd

