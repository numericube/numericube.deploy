# numericube.deploy

Provide generic base class for deploying application with fabric.

## Installation

 `pip install https://github.com/numericube/numericube.deploy/archive/master.zip`

## How to use numericube.deploy in your project

1. Create a fabfile directory in your repository
	`mkdir fabfile`

2. Create and edit __init__.py file in fabfile 
	   
       * For salt deployment copy and paste code localize in examples/salt/__init__.py
       * For ansible deployment copy and paste code localize in examples/ansible/__init__.py
	
3. Configure variable for your project

       * For salt deployment you can take example in  examples/salt/vars.yaml
       * For ansible deployment copy and paste code localize in examples/ansible/vars.yaml

## What provide numericube.deploy ?

numericube.deploy give some usefull function for deploying your project with fabric

    deploy          Perform a full LOCAL deploy on the given host.
    get_git_token   Prompt for git token and save it in ~/.fab_token.git
    help            print help
    latest_release  Return latest known release #
    release         Creates the release tag.
    test            Perform a Make test on the vagrant machine with current b...
    update_issues   Update issues according to what we're doing now.
 
 ## Can I extends numericube.deploy ?
 
 Yes ! add simply a new method in your class (example a custom bootstrap method for your project)
 You can override method if you want.
 
 
 
