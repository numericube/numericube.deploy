from setuptools import setup, find_packages
import os

version = '1.2'

setup(name='numericube.deploy',
      version=version,
      description="Numericube Deployment project",
      long_description=open("README.md").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='https://github.com/numericube/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['numericube'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'fabric',
          'github3.py',
          'pyyaml',
          'six',
          'packaging',
          'begins',
          'boto',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      create_instance = numericube.deploy.bin.ec2:create_instance.start
      """,
      )
