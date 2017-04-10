# where your repository is
# github.com-myproject is recognize by ssh config (see bellow)
GIT_REPOSITORY: {git_repository}
# location of private key for deployment (issue from deploy key of github)
SSH_CONFIG: {ssh_config}
SSH_KEY: {ssh_key}
# Debug mod
DEBUG: False
# Location of git_token
CREDENTIALS_FILE: ".git_token"
# Project name
PROJECT_NAME: {project_name}
# where the project is installed in remote dir
PROJECT_REMOTE_DIR: {project_remote_dir}
# deploy release update this file according this configuration
VERSION_FILE: {version_file}
# version key in yaml
KEY_VERSION_FILE: {key_version_file}
# relative location of inventory file of ansible
ANSIBLE_INVENTORY_FILE: {ansible_inventory_file}
# relative location of playbook
ANSIBLE_SITE: {ansible_site}
# location of public key for deployment
AUTHORIZED_KEY: {authorized_key}
# user used in deployment
USER: {user}
# what install for bootstrap
GENERIC_BOOTSTRAP:
  apt:
    - software-properties-common
    - python-software-properties
    - git
    - curl
