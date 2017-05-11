#!/bin/bash

# make all update
apt-get update -y
apt-get upgrade -y

# add user

adduser --disabled-password --gecos ""  {user}
adduser {user} sudo
mkdir /home/{user}/.ssh
chmod 700 /home/{user}/.ssh
echo "{public_key}" >> /home/{user}/.ssh/authorized_keys
chown -R {user}:{user} /home/{user}/.ssh
chmod 600 /home/{user}/.ssh/authorized_keys

# fix hostname
apt-get install curl
HOSTNAME=`curl http://169.254.169.254/latest/meta-data/public-hostname`
sed -i "127.0.1.1 $HOSTNAME" /etc/hosts
echo "$HOSTNAME" > /etc/hostname
hostname "$HOSTNAME"

# invit shell - set name of instance
sh -c 'echo "export NICKNAME={name}" > /etc/profile.d/prompt.sh'

# change sudoers
# change %sudo	ALL=(ALL:ALL) ALL
# TO
# %sudo ALL=(ALL) NOPASSWD:ALL
cp /etc/sudoers /etc/sudoers.bak
sed "s/.*%sudo.*/%sudo ALL=(ALL) NOPASSWD: ALL/g" /etc/sudoers > /tmp/sudoers.new
cp  /tmp/sudoers.new /etc/sudoers

