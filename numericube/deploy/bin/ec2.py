""" utility for ec2 create instance """

# -*- coding: utf-8 -*-
# Copyright (C) 2016 Numericube - all rights reserved
# No publication or distribution without authorization.
from __future__ import unicode_literals
import time;
import boto.ec2
import base64
import argparse
import begin

__author__ = 'yboussard'
__docformat__ = 'restructuredtext'


class EC2(object):
    """ helper class for create a new instance """

    instance_types = [{'type': 't1.micro',
                       'ECU': '<2',
                       'Mem': '0.613',
                       'Cost': '0.02'},
                      {'type': 't1.small',
                       'ECU': '1',
                       'Mem': '1.7',
                       'Cost': '0.08'},
                      {'type': 'm1.medium',
                       'ECU': '2',
                       'Mem': '3.75',
                       'Cost': '0.16'},
                      {'type': 'c1.medium',
                       'ECU': '5',
                       'Mem': '1.7',
                       'Cost': '0.165'}]

    ami = "ami-f2191786"
    key_name = "piper"
    security_groups = ['quick-start-1']

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        """ constructor """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.instance_type = 't1.micro'
        self.instance_name = 'selfpass'
        self.instance_shutdown_behavior = 'stop'

    def choice_instance(self):
        """ select instance """
        print '{:>30} {:>10} {:>10} {:>10}'.format('Instance type',
                                                   '#ECU',
                                                   'Mem',
                                                   'Cost')
        for inst_type in self.instance_types:
            print ("{type:>30} {ECU:>10} "
                   "{Mem:>10} {Cost:>10}").format(**inst_type)
        self.instance_type = raw_input('Which instance type do you want?'
                                       '(default t1.micro) ')
        if not self.instance_type:
            self.instance_type = 't1.micro'

    def choice_name(self):
        """ select name """
        self.instance_name = raw_input("Give your instance name ? "
                                       "(default selfpass)")
        if not self.instance_name:
            self.instance_name = 'selfpass'

    def choice_instance_behaviour(self):
        """ select instance behaviour """
        self.instance_shutdown_behavior = raw_input("Instance shutdown "
                                                    "behaviour "
                                                    "(stop or terminate) ? "
                                                    "(default stop)")
        if self.instance_shutdown_behavior:
            self.instance_shutdown_behavior = 'stop'

    def create_instance(self):
        """ create a new instance """
        # No more bootstrap, this done by numericube.deploy """
        self.choice_instance()
        self.choice_name()
        self.choice_instance_behaviour()
        print "Connecting AWS..."
        conn = boto.ec2.connect_to_region(
            "eu-west-1",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        start_time = time.time()
        print "Creating instance..."
        reservation = conn.run_instances(
            self.ami,
            key_name=self.key_name,
            instance_type=self.instance_type,
            security_groups=self.security_groups,
            instance_initiated_shutdown_behavior=self.instance_shutdown_behavior
        )
        instance = reservation.instances[0]
        # Check up on its status every so often
        print ("Waiting for instance to be created "
               "(this may take a few minutes)...")
        status = instance.update()
        while status == 'pending':
            time.sleep(10)
            status = instance.update()
        if status == 'running':
            instance.add_tag("Name", self.instance_name)
        else:
            print 'Instance status: ' + status
            raise NotImplementedError("Invalid status")
        elapsed = time.time() - start_time
        # Ok, the instance is up and running, now we configure it.
        print ("Your instance DNS name is: "
               "%s (elapsed %0.2f secs)") % (instance.public_dns_name, elapsed)
        print "You will receive an email when your instance is ready to work"


@begin.start
def create_instance(aws_access_key_id, aws_secret_access_key):
    """ create a new instances """
    ec2 = EC2(aws_access_key_id, aws_secret_access_key)
    ec2.create_instance()
