# -*- coding: utf-8 -*-
# Copyright (C) 2016 Numericube - all rights reserved
from __future__ import unicode_literals
import os
import sys
import shutil
from fabric.colors import red, green, blue, yellow

__author__ = 'yboussard'
__docformat__ = 'restructuredtext'

HERE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def question(label_question, title, exemple):
    """ generate a question """
    print ""
    print yellow(title)
    print blue("exemple: %s" % exemple)
    return raw_input(" %s ? " % label_question)

class Generator(object):

    def __init__(self):
        """ generate config file for numericube.deploy """
        if os.path.isdir('fabfile'):
            print red('Abort : fabfile directory exists !')
            sys.exit(-1)
        print green("Please configure some variables in order numericube.deploy "
                    "can work for your project ")
        self.project_name = question("Project Name",
                                     "Your project name",
                                     "myproject")
        self.project_remote_dir = question("Project path in remote "
                                           "machine",
                                           "Where source should be deploy "
                                           "on remote machine",
                                           "/project-src")
        self.ssh_config = question("Relative path to ssh config file",
                                   "Where is your ssh default config file",
                                   "../provision/ansible/roles/myproject/"
                                   "files/ssh_config")
        
        self.git_repository = question("Git repository",
                                       "According to your ssh config "
                                       "what's git repository name",
                                       "git@github.com-myproject:"
                                       "numericube/myproject.git")

        self.ssh_key = question("Relative path to ssh private key",
                                "Numericube.deploy use ssh key "
                                "to deploy application",
                                "../provision/ansible/roles/"
                                "myproject/files/ssh_key")
        
        self.authorized_key = question("Relative path to ssh public key",
                                       "Numericube.deploy use ssh key "
                                       "to deploy application",
                                       "../provision/ansible/roles/"
                                       "myproject/files/ssh_key.pub")
        
        self.version_file = question("Relative path to version file",
                                     "Numericube.deploy update version"
                                     "in a specific "
                                     "yaml ansible key",
                                     " ../provision/ansible/roles/"
                                     "myproject/vars/main.yml")
        self.key_version_file = question("Key version in ansible"
                                         " version_file ",
                                         "Numericube.deploy update version"
                                         " in a specific "
                                         "yaml ansible key",
                                         " myproject_version")
        self.user = question("User name used to deploy",
                             "Your app should be installed with "
                             "a specific user",
                             "project_user")
        self.ansible_inventory_file = question("Relative location of "
                                               "inventory file",
                                               "Please provide ansible "
                                               "host file "
                                               "relative location",
                                               "../provision/ansible/"
                                               "hosts")
        self.ansible_site = question("Relative location of ansible "
                                     "playbook",
                                     "Please provide location of ansible "
                                     "playbook (site.yml)",
                                     "../provision/ansible/site.yml")

        self.generate()

    def generate(self):
        """ generate configuration """
        with open(os.path.join(HERE, 'bin', 'template', 'vars.yaml.tpl')) \
             as template:
            content = template.read()
            content = content.format(
                project_name=self.project_name,
                project_remote_dir=self.project_remote_dir,
                ssh_config=self.ssh_config,
                git_repository=self.git_repository,
                ssh_key=self.ssh_key,
                authorized_key=self.authorized_key,
                version_file=self.version_file,
                key_version_file=self.key_version_file,
                user=self.user,
                ansible_inventory_file=self.ansible_inventory_file,
                ansible_site=self.ansible_site,
            )
            print yellow("Generated config file")
            print blue("======== BEGIN =============")
            print content
            print blue("======== END ===========")
            answer = raw_input(" DO YOU WANT GENERATE CONFIG for your project"
                               "(y/N) ? ")
            if answer.strip().lower() == 'y':
                print yellow('Create fabfile directory')
                os.mkdir('fabfile')
                with open('fabfile/vars.yaml', 'w') as configfile:
                    configfile.write(content)
                    print yellow("Have generated your config file")
                shutil.copy(os.path.join(HERE, 'bin', 'template',
                                         '__init__.py'),
                            'fabfile/__init__.py')
                print yellow("Your project is ready to use numericube.deploy")

def generator():
    """ generate a config file for numericube.deploy """
    generator_instance = Generator()
    

def old_generator():
    
    print green("Please configure some variables in order numericube.deploy "
                "can work for your project ")
    print yellow("Your project name")
    print blue(""" exemple : myproject""")
    project_name = raw_input(" Project Name ? ")
    print ""
    print yellow("Where source should be deploy on remote machine")
    print blue("Please see your ansible configuration")
    print blue(""" exemple : /project-src """)
    project_remote_dir = raw_input(" Project path in remote machine ? ")
    print "" 
    print yellow("Where your repository is the default config ssh to deploy")
    print yellow("We use and deploy ssh config file for deploying "
                 "your application on remote host")
    print blue(""" exemple : ../provision/ansible/roles/myproject/files/"""
               """:opt:myproject:.ssh:config""")
    ssh_config = raw_input(" Relative path to ssh config file ? ")
    print ""
    
    print yellow("According to your ssh config what'is your name of git "
                 "repository")
    print blue(""" exemple : """
               """ git@github.com-myproject:numericube/myproject.git """)
    git_repository = raw_input(" Git repository ? ")
    print ""
    
    print yellow("Numericube.deploy use ssh key (public and private) "
               "to deploy application "
               "in remote machine ")
    
    print blue(""" exemple : ../provision/ansible/roles/"""
               """myproject/files/"""
               """:opt:myproject:.ssh:myproject_rsa """)
    ssh_key = raw_input(" Relative path to ssh private key ? ")
    print blue(""" exemple :  ../provision/ansible/roles/myproject/files/"""
               """:opt:myproject:.ssh:myproject_rsa.pub""")
    authorized_key = raw_input(" Relative path to ssh public key ? ")
    print yellow("Numericube.deploy update version in a specific "
                 "yaml ansible key")
    print blue(" exemple:  ../provision/ansible/roles/myproject/vars/main.yml")
    version_file = raw_input(" Relative path to version file ? ")
    print ""
    print blue(" exemple:  project_version")
    key_version_file = raw_input(" Key version in ansible version_file "
                                 " ? ")
    print ""
    print yellow("Your app should be installed with a specific user")
    print blue(""" exemple :  myproject_user """)
    user = raw_input(" User name used to deploy ? ")
    print ""
    print yellow("Location of ansible inventory file")
    print blue(""" example  ../provision/ansible/hosts """)
    ansible_inventory_file = raw_input(" Relative location of inventory file "
                                       "of ansible ? (host file) ")
    print ""
    print yellow("Location of ansible playbook")
    print blue(""" example ../provision/ansible/site.yml """)
    ansible_site = raw_input(" Relative location of ansible playbook ? ")

    with open(os.path.join(HERE, 'bin', 'template', 'vars.yaml.tpl')) as template:
        content = template.read()
        content = content.format(project_name=project_name,
                                 project_remote_dir=project_remote_dir,
                                 ssh_config=ssh_config,
                                 git_repository=git_repository,
                                 ssh_key=ssh_key,
                                 authorized_key=authorized_key,
                                 version_file=version_file,
                                 key_version_file=key_version_file,
                                 user=user,
                                 ansible_inventory_file=ansible_inventory_file,
                                 ansible_site=ansible_site,
                                 )
        print yellow("Generated config file")
        print blue("======== BEGIN =============")
        print content
        print blue("======== END ===========")
        answer = raw_input(" DO YOU WANT GENERATE CONFIG for your project (y/N) ? ")
        if answer.strip().lower() == 'y':
            print yellow('Create fabfile directory')
            os.mkdir('fabfile')
            with open('fabfile/vars.yaml','w') as configfile:
                configfile.write(content)
                print yellow("Have generated your config file")
            shutil.copy(os.path.join(HERE, 'bin', 'template', '__init__.py'),
                       'fabfile/__init__.py')
            print yellow("Your project is ready to use numericube.deploy")
