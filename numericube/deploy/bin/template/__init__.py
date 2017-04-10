""" base class for numericube.deploy """
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from numericube.deploy.ansible import AnsibleDeployment
from numericube.deploy import utils

HERE = os.path.join(os.path.dirname(__file__))


class ProjectDeployment(AnsibleDeployment):
    """ specific task for Ansible deployment """

    def __init__(self):
        super(ProjectDeployment, self).__init__(
            HERE,
            os.path.join(HERE, 'vars.yaml'))

DEPLOY_INSTANCE = ProjectDeployment()
utils.add_class_methods_as_module_level_functions_for_fabric(DEPLOY_INSTANCE,
                                                             __name__)
