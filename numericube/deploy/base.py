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


import logging
logger = logging.getLogger("deploy")

import yaml
import os
import re
import time
import string
import urlparse
import logging
import yaml
from getpass import getuser, getpass

# import fabric
# from fabric.api import run
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
from fabric.decorators import runs_once
# from fabric.api import put
from fabric.api import env
from fabric.context_managers import quiet
from fabric.api import task
# from fabric.api import roles
from fabric.colors import red, green, blue, yellow
from fabric.contrib.console import confirm

try:
    import github3
    from github3 import authorize, GitHubError, login
except ImportError:
    print red("[ERROR] To have this script running properly, please do:")
    print "(sudo?) pip install github3.py"
    exit(-1)

COMMAND_CURRENT_BRANCH = r"git branch | grep '*' | sed -e 's/\* //g'"
COMMAND_CURRENT_TAG = r"git describe --exact-match --tags"


def create_release_number(git_branch=None):
    """Return release number according to date/time.
    If force_new is True, then we must provide a brand new and empty version #
    If svn_branch is give, we'll append last part
    of branch name to the release number
    """
    # Compute svn root and branch nickname
    branch_name = ""
    if git_branch:
        branch_name = os.path.basename(git_branch.strip("/"))
        if branch_name == 'master':
            branch_name = ""
    branch_name = branch_name and "-%s" % branch_name
    # Basic release # with extension letter
    release_number = "v%s" % time.strftime("%Y%m%d", time.localtime())
    addendums = ["", ] + list(string.lowercase)
    for addendum in addendums:
        extended = "%s%s%s" % (release_number, addendum, branch_name)
        has_release_number = local("git branch --list */%s -r" % extended,
                                   capture=True)
        if not has_release_number:
            return extended
    raise RuntimeError("More than 26 releases a day,"
                       "do you really think it's reasonable?...")

def my_two_factor_function():
    """ for github if we must have 2fa """
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = prompt('Enter 2FA code: ')
    return code

class BaseDeployment(object):
    """ base class for deployement """

    # Please define your variable in yaml config files
    project_remote_dir = None
    git_repository = None
    data_dir = None
    ssh_config = None
    ssh_key = None
    debug = False
    credentials_file = None
    common_ancestor_tag = None
    project_name = None
    # if you want add variable add to this

    def __init__(self, local_dir, yaml_config_file):
        """ load configuration of project by yaml
        @param local_dir: the location of deployment
        @param yaml_config_file : the location of configuration
        """
        self.local_dir = local_dir
        self.yaml_config_file = yaml_config_file
        with open(yaml_config_file) as yaml_config:
            config = yaml.load(yaml_config)
            for name in config.keys():
                self._load_config_var(config, name)
        self.current_branch = local(COMMAND_CURRENT_BRANCH,
                                    capture=True)
        print yellow("YOUR CURRENT BRANCH IS :"), \
            red("%s" % self.current_branch)

    def _load_config_var(self, config, name):
        """ populate instance state, abort if name is not
        defined in yaml file
        """
        if name not in config:
            print red('Your configuration file is incorect !'
                      'You must configure %s variable' % name)
            abort("Execution aborted")
        else:
            setattr(self, name.lower(), config[name])

    def help(self):
        """ print help """
        print yellow("Basic fabric scripts")
        print ""
        print green("REGULAR TRUNK DEPLOYMENT PROCESS")
        print green("--------------------------------")
        print yellow("fab "),green("release")
        print yellow("fab "),green("-H xxx-test deploy")
        print yellow("fab "),green("-H xxx-re-test deploy")
        print ""
        print red("YOUR -H OPTION MUST MATCH WHAT'S IN YOUR TOP.SLS FILES!!")
        print blue("In fact, the bootstrap process will even enforce "
                   "this in /etc/hostname and /etc/hosts.")
        print ""
        print green("BOOTSTRAPING A BRAND NEW MACHINE")
        print green("--------------------------------")
        print yellow("Bootstraping is automatic if no release "
                     "has been deployed on the target machine yet.")
        print yellow("However you need to provide initial credentials.")
        print yellow("Here's how to do so (you can omit the "
                     "-i <ssh_key> if you don't need one")

        print yellow("fab "), \
            green("-i ~/.ssh/private_key.pem -H user@host deploy")
        print ""
        print green("Deploying a specific tag on a specific host")
        print green("----------------------------------------------")
        print yellow("fab "),\
                     green("-H "),red("<host> "),\
                     green("deploy:release_number=v20170209a-develop")



    def latest_release(self):
        """Return latest known release #
        """
        # Get current branch
        with cd(self.local_dir):
            current_branch = self.current_branch
            if current_branch == 'master':
                branch_ext = ""
            else:
                branch_ext = '-%s' % current_branch

            # Fetch branches (locally, and sorted)
            local("git fetch", capture=True)
            cmd = (r"git tag --sort version:refname|"
                   r"grep 'v[0-9]\{8\}[a-z]\?%s'")
            with quiet():
                tags = local(cmd % branch_ext, capture=True)
            if tags.failed:
                self._raise_no_valid_tag()
            else:
                tag = tags.split("\n")[-1]
                if tag:
                    print blue("Latest release tag is"), yellow(tag) 
                    return tag
                else:
                    self._raise_no_valid_tag()

    def _raise_no_valid_tag(self):
        """ return message for no valid tag  """
        msg = ("No valid release tag here: %s. "
               "Use 'fab release' to create one.") % self.git_repository
        print red(msg)
        raise RuntimeError(msg)

    def _get_release_tag(self, release_number):
        """ Return release tag according to root and release """
        local("git fetch")
        cmd = "git tag --sort version:refname -l %s" % release_number
        with quiet():
            tag = local(cmd, capture=True)
            return tag 
        if tag.failed:
            self._raise_no_valid_tag()

    def test(self):
        """Perform a Make test on the vagrant machine with current branch.
        """
        self._bootstrap_fqdn()
        print green("ok %s" % env.host_string)

    def _create_release_number(self, git_branch=None):
        """Return release number according to date/time.
        If force_new is True, then we must provide a brand
        new and empty version #
        If svn_branch is give, we'll append last part
        of branch name to the release number
        """
        # Compute git_branch nickname
        tag_name = ""
        if git_branch:
            tag_name = os.path.basename(git_branch.strip("/"))
        if tag_name == 'master':
            tag_name = ""
        tag_name = tag_name and "-%s" % tag_name
        # Basic release # with extension letter
        release_number = "v%s" % time.strftime("%Y%m%d", time.localtime())
        addendums = ["", ] + list(string.lowercase)
        for addendum in addendums:
            extended = "%s%s%s" % (release_number, addendum, tag_name)
            cmd_release = "git tag --sort version:refname -l %s"
            has_release_number = local(cmd_release % extended,
                                       capture=True)
            if not has_release_number:
                return extended
        raise RuntimeError("More than 26 releases a day,"
                           "do you really think it's reasonable?...")

    def _check_git_ready(self, src_path):
        """Prepare a release candidate version.
        This just performs TESTS on your current git branch.
        This process checks that:
        - git is commited
        - no pdb in src
        """
        # Get remote content
        with lcd(src_path):
            with quiet():
                local("git fetch origin", capture=True)
        # Check that git is commited and up-to-date
        with lcd(src_path):
            with quiet():
                output = local("git status --porcelain", capture=True)
            if output.strip() or output.return_code:
                print yellow(output)
                print red("RELEASE ERROR: You must 'git commit' and "
                          "git push origin'"
                          "your code before testing a release candidate.")
                if self.debug is False:
                    abort("RELEASE ERROR: You must update and commit your code"
                          "before testing a release candidate.")

        # verify local and remote are ready
        with lcd(src_path):
            with quiet():
                current_branch = self.current_branch
                output = local("git branch -av --list *%s" % current_branch,
                               capture=True)
                lines = output.split("\n")
                # remove release branch
                local_remote = []
                for line in lines:
                    # get only branch that match branch name.
                    # Sorry for the double split (ain't got much time)
                    # print line[2:].split(' ')[0].split('/')[-1]
                    if current_branch == line[2:].split(' ')[0].split('/')[-1]:
                        local_remote.append(line)
                        # if not re.compile('v[0-9]{8}')\
                        #.findall(line[2:].split(' ')[0]):
                        #     local_remote.append(line)

                # Now there should be 2 lines, one being
                # local and the other being remote
                if len(local_remote) != 2:
                    print yellow(output)
                    print yellow("\n".join(local_remote))
                    msg = ("RELEASE ERROR: NO REMOTE BRANCH ! You must "
                           "'git push --set-upstream origin <branch_name>'"
                           "your code before testing a release candidate.")
                    print red(msg)
                    abort(msg)

                # Ok, we have our 2 branches. Now compare last release numbers.
                # Here's an example of what we've got to deal with:
                # * develop                4ff335b Added dummy file
                #   remotes/origin/develop 4ff335b Added dummy file
                # We check the sha (7 characters),
                #but as the branch name itself could match an sha pattern,
                # we check for a match that is not preceded by a '*' character!
                try:
                    sha_pattern = re.compile(r'(?<!\*)\s[a-z-0-9]{7}\s')
                    assert sha_pattern.findall(local_remote[0]) \
                        == sha_pattern.findall(local_remote[1])
                except AssertionError:
                    print yellow(output)
                    msg = ("RELEASE ERROR: You must 'git push origin'"
                           "your code before testing a release candidate."
                           "local and remote is not in the same state")
                    print red(msg)
                    abort(msg)
        # Check against remainging PDBs
        with lcd(src_path):
            with quiet():
                result = local(r"""egrep -RI "^[^#]*set_trace" *""",
                               capture=True)
                print ("(you can safely ignore if the 'egrep' "
                       "command itelf returns an error)")
                if result.return_code == 0:
                    print red("THERE IS STILL PDB IN YOUR CODE!"
                              "CORRECT THIS URGENTLY, YOUR SERVER"
                              "IS AT RISK!!!")
                    print red("================"
                              "================"
                              "================"
                              "================"
                              "================")
                    print red(result)
                    if not self.debug:
                        raise RuntimeError("Please remove PDB breakpoints"
                                           "from your code.")

    def _bump_version(self, src_dir, git_release_tag, release_number):
        """Bump version in files, return the list of files about to be commited
        """
        raise NotImplementedError("You must define this method in subclass")

    def release(self):
        """ Creates the release tag.
        This task will:
        - Create a release number (v20140901) with localbranch
          or append a label name if necessary (eg. v20140901-pomona_ta)
        - Update bump_version
          GIT branch number match what's given
        - Perform an creation of tag release number.
        """
        src_dir = os.path.abspath(os.path.join(self.local_dir, ".."))
        self._check_git_ready(src_dir)

        # get the local branch
        git_branch = self.current_branch
        release_number = self._create_release_number(git_branch)
        git_release_tag = release_number
        print blue("[RELEASE] Preparing release of the ") \
            + release_number + blue(" version.")

        # We create new branch and then bump versions inside this branch
        self._check_git_ready(src_dir)
        current_branch = self.current_branch
        with lcd(src_dir):
            # if there is a local branch merge else create branch and commit
            # If you have an error with git tag,
            # follow what's said here:
            #  https://nathanhoad.net/how-to-delete-a-remote-git-tag
            # Bump version in files
            to_commit = self._bump_version(src_dir,
                                           git_release_tag,
                                           release_number)

            # Commit pillar file into GIT
            have_to_push = False
            for fname in to_commit.split("\n"):
                have_to_push = True
                local("git add %s" % (fname[2:], ))
            if have_to_push is True:
                local("git commit -am 'Preparing %s tag provisioning'"
                      % (git_release_tag,))
            local("git push origin %s" % current_branch)
            local("git tag -a %s -m 'Tagging %s branch'"
                  % (release_number, release_number))
            local("git push --tags")
        # Greetings message
        print green("Ok, your tag ") \
            + release_number \
            + green(" is ready to be deployed.")
        default_hostname = env.hosts and env.hosts[0]
        print green("Run ") \
            + "fab -H " \
            + yellow(default_hostname) \
            + " deploy:%s" % release_number \
            + green(" to deploy your new tag on any server.")
        print

        # Ask for service
        if not confirm("Do you want to deploy this version on a server?",
                       default=False):
            abort("Ok. You can always do so later anyway.")
        host = prompt("Which hostname would you like to deploy to?",
                      default=default_hostname)
        env.hosts = [host]
        execute(self.deploy, release_number)

    def _populate_git_key(self):
        """ put to remote host deploy key in order to git working """
        print "Putting ssh private key in .ssh in remote host..."
        if not exists("/root/.ssh", use_sudo=True):
            sudo("mkdir /root/.ssh")
        put(os.path.join(self.local_dir, self.ssh_config), '/root/.ssh/config',
            use_sudo=True)
        put(os.path.join(self.local_dir,self.ssh_key),
            '/root/.ssh/%s_rsa' % self.project_name,
            use_sudo=True)
        sudo("chown root:root /root/.ssh/config")
        sudo("chown root:root /root/.ssh/%s_rsa" % self.project_name)
        sudo("chmod 600 /root/.ssh/config")
        sudo("chmod 600 /root/.ssh/%s_rsa" % self.project_name)
        if not exists('/root/.ssh/known_hosts'):
            sudo("ssh-keyscan github.com >> /root/.ssh/known_hosts")
        if not sudo("grep github.com /root/.ssh/known_hosts"):
            sudo("ssh-keyscan github.com >> /root/.ssh/known_hosts")

    def bootstrap(self):
        """Bootstrap the given host so it can be used with our release system.
        The tricky part here is to handle more-or-less authentication."""
        raise NotImplementedError('Please implements in subclass this method')

    def _bootstrap_ubuntu_essential(self):
        """ install essential pkg for bootstraping """
        with quiet():
            ret = sudo("ls")
        if ret.failed:
            run("apt-get install -y sudo")
        #  (see
        #   http://docs.saltstack.com/en/latest/topics/installation/ubuntu.html)
        sudo("apt-get update -y")
        for pkg in self.generic_bootstrap['apt']:
            sudo("apt-get install -y %s" % pkg)
            # for install the last stable version of git
            # sudo("sudo add-apt-repository ppa:git-core/ppa -y")

    def _bootstrap_fqdn(self):
        """ check bootstrap fqdn """
        # DOUBLE CHECK FQDN!!!!!!!!!!
        # IF FQDN DOESN'T MATCH IT MAY INDICATE THERE'S
        # SOMETHING WRONG IN THE PROCESS.
        fqdn = run("""python -c "import socket;print socket.getfqdn()" """)
        fqdn = fqdn.strip()
        target_fqdn = urlparse.urlparse("ssh://%s" % env.host_string).hostname
        # To do so: socket.getfqdn()
        if fqdn != target_fqdn:
            print red("FQDN for your target machine doesn't match "
                      "the -H %s you provided" % target_fqdn)
            print yellow("  target FQDN:"), target_fqdn
            print yellow("  actual FQDN:"), fqdn
            print yellow("  Edit target's /etc/host and /etc/hostname "
                         "to make it match your target string.")
            abort("Too risky to continue "
                  "if you don't even know your machine's correct FQDN ;)")

        # Set hostname et al. IIF necessary
        # SEE
        # http://askubuntu.com/questions/9540/how-do-i-change-the-computer-name

    def _get_remote_current_tag(self):
        """ Retrieve current tag number or the target machine """
        with cd(self.project_remote_dir):
            current_tag = sudo(COMMAND_CURRENT_TAG, warn_only=True,
                               user=self.user)
        if 'git: command not found' in current_tag:
            print red("Git is not installed on %s" % env.host_string)
            current_tag = None
            return current_tag
        if not re.compile('v[0-9]{8}').findall(current_tag):
            current_tag = None
        if current_tag is None:
            with cd(self.project_remote_dir):
                current_tag = sudo(COMMAND_CURRENT_BRANCH, warn_only=True,
                                   user=self.user)
            if not re.compile('v[0-9]{8}').findall(current_tag):
                return None
            else:
                print red("WARNING:"), "your remote repository ", \
                    "is based on git branch ",yellow(current_tag), \
                    " not a git tag"
                print red("You are notice that deploy process switch "
                          "now with a tag (not a branch)")
                if not confirm("Do you aggree with that ?",
                               default=True):
                    abort("Ok. You can manually switch "
                          "to a tag on remote server")
        # Return it
        return current_tag

    def _review_diffs(self, current_tag, git_release_tag, from_deploy=True):
        """A helper method to give a prompt and review diffs or confirm/abort.
        Will diff commit hashes or refuse executing.
        """
        # No current_tag? Well that's probably beacuse we're bootstrapping
        if not current_tag:
            print red("  NOTHING DEPLOYED ON THE TARGET SERVER (yet?)")
            return confirm("Do you want to deploy anyway?")
        # Append "origin" to the branches
        # (just in case the current_tag is not local)
        #if not current_tag.startswith("origin/"):
        #    current_tag = "origin/%s" % current_tag
        #if not git_release_tag.startswith("origin/"):
        #    git_release_tag = "origin/%s" % git_release_tag

        # Compute applicable diffs
        with settings(warn_only=True):
            avail_diff = local(
                """git log %s..%s --pretty="format:%%h" """
                % (current_tag, git_release_tag),
                capture=True,
            )
            if not avail_diff:
                print avail_diff.stderr
            avail_diff = avail_diff.split()

        # No available diff? Well that's sad.
        if not avail_diff:
            print yellow("Oups... No history available. Sorry "
                         "for that. Maybe because you have a lot"
                         " of nested merges.")
            print red("DOUBLE CHECK YOUR REVISIONS TO AVOID ANY ERRORS.")
        # Message loop
        while True:
            # Display a nice history if applicable
            if avail_diff:
                if current_tag and git_release_tag:
                    local(
                        """git log %s..%s --left-right --graph """
                        """--pretty="format:%%h | %%C(yellow)%%ci%%Creset"""
                        """| %%s %%C(yellow)[%%cn]%%Creset" """ % (
                            current_tag,
                            git_release_tag,
                        )
                    )
            if from_deploy:
                answer = prompt("Type a commit hash to perform a diff,"
                                "'no' to abort, 'yes' to deploy or "
                                "'hotfix' to perform a hotfix:").strip()
            else:
                answer = prompt("Type a commit hash to perform "
                                "a diff or 'yes' to stop:").strip()
            # Commit number? Yeaaah, rock it, baby!
            try:
                diff_index = avail_diff.index(answer)
                if diff_index >= (len(avail_diff) - 1):
                    previous_tag = current_tag
                else:
                    previous_tag = avail_diff[diff_index + 1]
                local("""git diff %s..%s"""
                      % (previous_tag, avail_diff[diff_index]))
            except ValueError:
                pass
            # Expected answer: say we're happy
            if answer == 'yes':
                return True
            elif answer == 'no':
                return False
            elif answer == 'hotfix':
                return 'hotfix'

    def deploy(self, release_number=None, hotfix=False):
        """Perform a full LOCAL deploy on the given host.
        This will:
        - Update git to make the platforms tag
          match the release_number we're going for
        - SSH to the host machine and perform actual git up/switch
        - ...then perform the provisionning with the new version set.
        """
        # Find release number or branch.
        # If no release_number given, will use latest version
        if not release_number:
            release_number = self.latest_release()
        git_release_tag = self._get_release_tag(release_number)

        # Print information about found branch
        try:
            print green("Deploying %s" % (git_release_tag,))
        except:
            print red("The release tag %s likely doesn't exist. "
                      "Run 'fab release' before." % git_release_tag)
            raise

        # Try to guess which version is currently deployed on the remote server
        current_tag = self._get_remote_current_tag()
        # Greetings message
        print yellow("******************************")
        print yellow("**  %s DEPLOYMENT   **" % self.project_name.upper())
        print yellow("******************************")
        print yellow("")

        # DOUBLE CHECK CURRENT BRANCH AGAINST RELEASE NUMBER.
        # If there's a difference, display a red flag
        if not current_tag:
            print red("No current branch deployed on %s" % env.host_string)
            print red("BE VERY CAREFUL, THIS MIGHT INDICATE A PROBLEM "
                      "WITH DEPLOYMENT.")
        elif "-" in current_tag and "-" not in release_number:
            print red("BRANCH CHANGE ON: %s" % env.host_string)
            print red("BE VERY CAREFUL, THIS MIGHT "
                      "INDICATE A PROBLEM WITH DEPLOYMENT. "
                      "CHECK THE BRANCH YOU'RE DEPLOYING.")

        # Pause, display a nice message telling what's about to be done
        print ("IF YOU'RE WORKING WITH THE PRODUCTION "
               "SETTINGS, BE EXTREMELY CAREFUL.\n")
        if not current_tag:
            print yellow("WARNING: THE HOST HAS APPARENTLY NO "
                         "VERSION DEPLOYED SO WE WILL BOOTSTRAP IT.")
        print "%s %s %s" % (yellow("You're about to deploy"),
                            green(release_number),
                            yellow("on the following host:"))
        print "%s %s %s" % (yellow("   => "),
                            yellow("%64s" % (env.host_string,)),
                            "[%s  => %s ]" % \
                            (green(current_tag),green(git_release_tag)))
        print ""
        # Ask for confirmation and ask for the opportunity to review diffs
        answer = self._review_diffs(current_tag, git_release_tag)
        if not answer:
            print "You might run it again with:"
            print yellow("    fab -H %s deploy:%s" % (env.host_string,
                                                      release_number))
            abort("Execution aborted.")
        if answer == 'hotfix':
            hotfix = True
        # Install bootstrap if necessary
        if not current_tag:
            execute(self.bootstrap)

        # Configure ssh key for git for root user (use bellow)
        self._populate_git_key()

        self._configure_provising(git_release_tag)
        # Configure salt minion, and deploy svn to use the branch version
        # configure_minion(git_release_tag, release_number)

        # Run it, baby!
        if hotfix:
            self._hot_fix_provisioning()
        else:
            self._provisioning()

        # And now, ladies and gentlemen,
        # update issues about what we've just done!
        self.update_issues(current_tag, git_release_tag)

    def _configure_provising(self, git_release_tag):
        """ task for deploying on platform """
        raise NotImplementedError("You must implement this in order to deploy")

    def _hot_fix_provisioning(self):
        """ run hot fix command """
        raise NotImplementedError("You must implement _hot_fix_provisioning "
                                  "in subclass")

    def _provisioning(self):
        """ run deploy command """
        raise NotImplementedError("You must implement _provisioning "
                                  "in subclass")

    def _git_update_issues_var(self):
        """ return information usefull for update_issues """
        repository = self.git_repository
        (root, project_name) = repository.split(':')[1].split('/')
        project_name = project_name.replace('.git', '')
        return (root, project_name)

    def update_issues(self, git_previous_tag=None, git_release_tag=None):
        """Update issues according to what we're doing now.
        """
        # Prepare text to put in the issues
        issue_comment = ("Tag %s deployed on"
                         "http://%s by %s") % (git_release_tag,
                                               env.host_string,
                                               getuser())
        try:
            issue_label = env.host_string.split('.')[0]
        except:
            print red('You must provide a valid host ! -H parameter')
            abort('host is empty')
        if git_previous_tag is None or git_release_tag is None:
            print red('You must provide a  git_previous_tag and '
                      'a  git_release_tag ')
            print yellow("Usage: fab -H host update_isssues:"
                         "git_previous_tag=<>,git_previous_tag=<>")
            abort('Invalid parameters')
        if confirm("Do you want to update git tracker about this release ?",
                   default=True) is False:
            print blue('*** end ***')
            return
        # Retreive diff
        with settings(warn_only=True):
            avail_diff = local(
                """git log %s..%s --pretty="oneline" """
                % (git_previous_tag,
                   git_release_tag),
                capture=True,
            )
            if not avail_diff:
                print avail_diff.stderr
            avail_diff = unicode(avail_diff, 'utf8').split("\n")

        # Scan issues inside log (freshest first)
        github = login(token=self.get_git_token())
        root, project_name = self._git_update_issues_var()
        for line in avail_diff:
            for issue_id in re.findall(r"#([0-9]+)\b", line):
                issue = github.issue(root, project_name, issue_id)
                if not issue:
                    continue

                # Update issue with comment and label
                if issue_label not in [line.name for line in issue.labels]:
                    print green("   Deployed:"), line[41:]
                    issue.create_comment(issue_comment)
                    issue.add_labels(issue_label)

    def get_git_token(self, user='', password=''):
        """Prompt for git token and save it in ~/.fab_token.git
        """
        # Read token for file, return it if we already got it
        token = ''
        try:
            with open(os.path.join(self.local_dir,
                                   self.credentials_file), 'r') as fd_git:
                token = fd_git.readline().strip()  # Can't hurt to be paranoid
                # id = fd.readline().strip()
        except IOError:
            pass
        if token:
            return token
        # Taken from
        # http://github3py.readthedocs.io/en/latest/examples/oauth.html
        while not user:
            user = prompt("Please enter your github username",
                          default=getuser())
        while not password:
            password = getpass('Please enter your github password for {0}: '
                               .format(user))
        # Compute token
        note = 'Fab release by N3'
        note_url = 'http://numericube.com'
        scopes = ['user', 'repo']
        try:
            auth = authorize(user, password, scopes, note, note_url,
                             two_factor_callback=my_two_factor_function)
            with open(os.path.join(self.local_dir,
                                   self.credentials_file), 'w') as fdgit:
                fdgit.write(auth.token + '\n')
                # fd.write(auth.id)
        except GitHubError as exception:
            if exception.message == "Bad credentials":
                print red("ERROR: Invalid GitHub credentials")
                exit(0)
            elif exception.message == 'Validation Failed':
                # We probably already have an auth, find it back,
                # delete it and start again
                gith = github3.login(user, password)
                for auth in gith.iter_authorizations():
                    if (auth.note == note) and (auth.note_url == note_url):
                        auth.delete()
                        return self.get_git_token(user, password)
            # If we reach here, we just raise
            raise
        # Just return our token
        return auth.token
