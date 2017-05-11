""" numericube base deployment """
# -*- coding: utf-8 -*-
# Copyright (C) 2016 Numericube - all rights reserved
# No publication or distribution without authorization.
from __future__ import unicode_literals

__author__  = 'yboussard'
__docformat__ = 'restructuredtext'
__copyright__ = "Copyright 2013-2016, NumeriCube"
__license__ = "CLOSED SOURCE"
__version__ = "TBD"
__maintainer__ = "Pierre-Julien Grizel"
__email__ = "pjgrizel@numericube.com"
__status__ = "Production"

import os
import re
import yaml
import logging
logger = logging.getLogger("deploy")
from numericube.deploy import base
from fabric.api import settings
from fabric.api import sudo, run
from fabric.api import cd
from fabric.api import lcd
from fabric.api import local
from fabric.api import put
from fabric.api import execute
from fabric.api import abort
from fabric.api import prompt
from fabric.contrib.files import exists
from fabric.colors import red, green, blue, yellow
from fabric.contrib.console import confirm
from fabric.context_managers import quiet


class SaltDeployment(base.BaseDeployment):
    """ class for salt deployment """

    version_file = None
    remote_minion_target = None

    def _bump_version(self, src_dir, git_release_tag, release_number):
        """Bump version in files, return the list of files about to be commited
        """
        # First of all, we update version number in monespace/init.sls,
        # so that the branch we're creating will be deployed.
        pillar_filename = os.path.join(self.local_dir,
                                       self.version_file)
        # Load our pillar file and carefuly replace what needs to be replaced
        with open(pillar_filename, "r") as pillar_file:
            pillar = yaml.load(pillar_file)
        # Indicate active version in our pillar file and save it back.
        try:
            current_version = pillar['project']['deployed_branch']
        except KeyError:
            raise RuntimeError("Your pillar file not have a good structure"
                               "Must have 'project' section and "
                               "'deployed_branch' key")
        if not current_version:
            raise RuntimeError("Invalid data for "
                               "yaml file: %s" % pillar_filename)
        pillar['project']['deployed_branch'] = str(git_release_tag)
        with open(pillar_filename, "w") as pillar_file:
            yaml.safe_dump(pillar, default_flow_style=False, stream=pillar_file)

        # Same for setup.py file, we update the __version__ variable
        setup_filename = os.path.join(src_dir, "setup.py")
        lines = []
        with open(setup_filename) as infile:
            for line in infile:
                line = re.sub("__version__.*=.*",
                              "__version__ = '%s'" % release_number, line)
                lines.append(line)
        with open(setup_filename, 'w') as outfile:
            for line in lines:
                outfile.write(line)
        # Return files to commit
        to_commit = local("git status -s", capture=True)
        return to_commit

    def _bootstrap_ubuntu_salt(self):
        """ specific bootstrap for salt """
        # bootstrap salt minion
        # on debian weezy please read https://repo.saltstack.com/#debian
        try:
            sudo("apt-get install -y salt-minion")
        except:
            print yellow("Can not found salt-minion ,"
                         "install via bootstrap is more secure")
            sudo('wget -O bootstrap_salt.sh https://bootstrap.saltstack.com')
            sudo('sh bootstrap_salt.sh -P git v2016.3.3')

    def _configure_provising(self,  git_release_tag):
        """ Setup /srv/ directory on the target machine """

        # remote_minion_target is /srv/ see vars.yaml
        if not exists(os.path.join(self.remote_minion_target,
                                   '.git'), use_sudo=True):
            with cd(self.remote_minion_target):
                sudo("git init .")
        # first time if /srv/pillar is not a symbolic link but an svn repository
        with cd(self.remote_minion_target):
            print yellow("Update salt part with tag %s" % git_release_tag)
            with quiet():
                sudo("git remote add origin %s" % self.git_repository)
            # add config file on .ssh
            sudo("git config core.sparsecheckout true")
            sudo("echo provision/pillar >> .git/info/sparse-checkout")
            sudo("echo provision/salt >> .git/info/sparse-checkout")

            #sudo("ssh -T git@github.com-monespace")
            # if there is local change we erase it
            try:
                sudo("git fetch")
                sudo("git checkout -f %s" % git_release_tag)
            except:
                if confirm("There is local change in /srv, "
                           "do you want reset them ?"):
                    sudo("sudo git reset --hard")
                    sudo("git fetch")
                    sudo("git checkout %s" % git_release_tag)
            for salt_part in ("salt", "pillar"):
            # if there is not symbolic link we create it
                if not exists(os.path.join(self.remote_minion_target,
                                           salt_part), use_sudo=True):
                    sudo("ln -s provision/%s %s" % (salt_part, salt_part))
                if not sudo("if [ -L %s ]; then echo 'ok';fi" % (salt_part,) ):
                    msg = ("Directory /%s/%s is not a symbolic link "
                           "to /%s/provision/%s")
                    msg = msg % (self.remote_minion_target,
                                 salt_part,
                                 self.remote_minion_target,
                                 salt_part)
                    print red(msg)
                    abort(msg)

    def _provisioning(self):
        """ run provisioning """
        salt_return = sudo("salt-call --local state.highstate")
        pattern = re.compile(r'Failed:\s+(\d+)')
        if pattern.search(salt_return):
            failed = int(pattern.search(salt_return).groups()[0])
            if self.debug is False and failed != 0:
                print red('There is %d failed states  , abort' % failed)
                abort("There is a problem in deploy")
        else:
            print red('No summary returned by salt, problem with salt, abort')
            abort("There is a problem in deploy")

    def bootstrap(self):
        """ bootstrap project """
        self._bootstrap_fqdn()
        self._bootstrap_ubuntu_essential()
        self._bootstrap_ubuntu_salt()
        sudo("mkdir -p %s" % self.remote_minion_target)
        # Reset minion id
        sudo("rm -f /etc/salt/minion_id")
