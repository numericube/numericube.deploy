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


class AnsibleDeployment(base.BaseDeployment):
    """ class for salt deployment """

    salt_version_file = None
    remote_minion_target = None
    authorized_key = None
    attributes = base.BaseDeployment.attributes + ('AUTHORIZED_KEY',
                                                   'VERSION_FILE',
                                                   'KEY_VERSION_FILE')

    
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
        current_version = main_data[self.KEY_VERSION_FILE]
        if not current_version:
            raise RuntimeError("Invalid data for yaml file: %s" % main_data)
        main_data[self.KEY_VERSION_FILE] = git_release_branch
        with open(main_filename, "w") as main_file:
            yaml.dump(main_data, default_flow_style=False, stream=main_file)
    
        # Same for setup.py file, we update the __version__ variable
        setup_filename = os.path.join(src_dir, "src", "setup.py")
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

    def _configure_provising(self,  git_release_tag):
        """ Setup /srv/ directory on the target machine """
        try:
            with cd(self.local_dir):
                local("ansible-playbook  --limit='%s' "
                      "--inventory-file=%s "
                      "--sudo -vvv %s "
                      "--list-hosts" % (self.ansible_host,
                                        self.ansible_site,
                                        env.host_string))
        except:
            print red("ANSIBLE ERROR: please fix that (Please see bellow)")
            message = ("Execution aborted. Have you define "
                       "host %s  in ./provision/ansible/hosts ?. "
                       "If no please configure it !") % env.host_string
            print red(message)
            abort(message)
        
            
        
        
    def _hot_fix_provisioning(self):
        """ call provising on sources """
        pass

    def _provisioning(self):
        """ run provisioning """
        
        local("ansible-playbook --limit='%s'  "
              "--inventory-file=%s "
              "--sudo -vvv %s  "
              "--private-key=%s -u ansible -c paramiko" % (env.host_string,
                                                           self.ansible_inventory_file,
                                                           self.ansible_site,
                                                           self.ssh_key))

