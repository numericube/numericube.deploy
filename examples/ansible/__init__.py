# -*- coding: utf-8 -*-
# Copyright (C) 2016 Numericube - all rights reserved
# No publication or distribution without authorization.
from __future__ import unicode_literals
import os
from numericube.deploy.ansible import AnsibleDeployment
from numericube.deploy import utils
from fabric.api import sudo


HERE = os.path.join(os.path.dirname(__file__))

class ProjectDeployment(AnsibleDeployment):
    """ specific task for monespace """

    def __init__(self):
        return super(AnsibleDeployment, self)\
            .__init__(HERE,
                      os.path.join(HERE,'vars.yaml'))

    
deploy = ProjectDeployment()
utils.add_class_methods_as_module_level_functions_for_fabric(deploy, __name__)

