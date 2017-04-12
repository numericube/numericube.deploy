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
from fabric.api import env


class AnsibleDeployment(base.BaseDeployment):
    """ class for salt deployment """

    salt_version_file = None
    remote_minion_target = None
    authorized_key = None
    
    def _bump_version(self, src_dir, git_release_tag, release_number):
        """Bump version in files, return the list of files about to be commited
        """
        import yaml

        # First of all, we update version number in monespace/init.sls,
        # so that the branch we're creating will be deployed.
        main_filename = os.path.join(os.path.join(self.local_dir,
                                                  self.version_file))
        # Load our pillar file and carefuly replace what needs to be replaced
        with open(main_filename, "r") as main_file:
            main_data = yaml.load(main_file)
        # Indicate active version in our main file and save it back.
        current_version = main_data[self.key_version_file]
        if not current_version:
            raise RuntimeError("Invalid data for yaml file: %s" % main_data)
        main_data[self.key_version_file] = git_release_tag
        with open(main_filename, "w") as main_file:
            yaml.dump(main_data, default_flow_style=False, stream=main_file)
    
        # Same for setup.py file, we update the __version__ variable
        setup_filename = self._find_setup_filename(src_dir)
        lines = []
        with open(setup_filename) as infile:
            for line in infile:
                line = re.sub("__version__.*=.*",
                              "__version__ = '%s'" % release_number, line)
                lines.append(line)
        with open(setup_filename, 'w') as outfile:
            for line in lines:
                outfile.write(line)
        to_commit = local("git status -s", capture=True)
        return to_commit

    def _find_setup_filename(self, src_dir):
        """ return setup.py for project """ 
        if os.path.exists(os.path.join(src_dir, "src", 'setup.py')):
            return os.path.join(src_dir, "src", 'setup.py')
        elif os.path.exists(os.path.join(src_dir, 'setup.py')):
            return os.path.join(src_dir, 'setup.py')
        else:
            RuntimeError("ABORT Can't find a valid setup.py is %s" % src_dir)

    def _configure_provising(self,  git_release_tag):
        """ Setup /srv/ directory on the target machine """
        try:
            with cd(os.path.join(self.local_dir, '..')):
                local("ansible-playbook  --limit='%s' "
                      "--inventory-file=%s "
                      "--sudo -vvv %s "
                      "--list-hosts" % (env.host_string,
                                        os.path.join(self.local_dir,
                                                     self.ansible_inventory_file),
                                        os.path.join(self.local_dir,
                                                     self.ansible_site),
                                        ))
        except:
            print red("ANSIBLE ERROR: please fix that (Please see bellow)")
            message = ("Execution aborted. Have you define "
                       "host %s  in ./provision/ansible/hosts ?. "
                       "If no please configure it !") % env.host_string
            print red(message)
            abort(message)

    def _add_ansible_user(self):
        """ create ansible user """
        with quiet():
            sudo("useradd ansible -m  -s /bin/bash")
            sudo("echo 'ansible ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers")
        with quiet():
            sudo("mkdir /home/ansible/.ssh/", user="ansible")
            put(os.path.join(self.local_dir,self.authorized_key), '/home/ansible/.ssh/authorized_keys2',
                mode=0600,
                use_sudo=True)
        local("chmod 600 %s" % os.path.join(self.local_dir, self.ssh_key))
        sudo("chown ansible /home/ansible/.ssh/authorized_keys2")

    def bootstrap(self):
        """ bootstrap project """
        self._bootstrap_fqdn()
        self._bootstrap_ubuntu_essential()
        self._add_ansible_user()

    def _provisioning(self):
        """ run provisioning """
        with cd(os.path.join(self.local_dir, '..')):
            local("ansible-playbook --limit='%s'  "
                  "--inventory-file=%s "
                  "--sudo -vvv %s  "
                  "--private-key=%s -u ansible -c paramiko" % (env.host_string,
                                                               os.path.join(self.local_dir,
                                                                            self.ansible_inventory_file),
                                                               os.path.join(self.local_dir,
                                                                            self.ansible_site),
                                                               os.path.join(self.local_dir,
                                                                            self.ssh_key)))
