# -*- coding: utf-8 -*-
# Copyright (C) 2016 Numericube - all rights reserved
# No publication or distribution without authorization.
from __future__ import unicode_literals
import os
from numericube.deploy.salt import SaltDeployment
from numericube.deploy import utils


HERE = os.path.join(os.path.dirname(__file__))

class MySaltDeployment(SaltDeployment):
    """ specific task for myproject """

    def __init__(self):
        # load all variable in instance
        # each of them become an attribute of instance
        # for exemple if you define MY_VARIABLE in your config file
        # you can use self.my_variable in your instance
        return super(MySaltDeployment, self)\
            .__init__(HERE,
                      os.path.join(HERE,'vars.yaml'))
        
deploy = MySaltDeployment()
utils.add_class_methods_as_module_level_functions_for_fabric(deploy, __name__)

    
