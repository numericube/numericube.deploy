# numericube.deploy

   Provide generic base class for deploying application (based on salt or ansible) with fabric.

## Install

 `git clone git@github.com:numericube/numericube.deploy.git`
 
 `pip install -r ./numericube.deploy/requirements.txt`
 
 `pip install ./numericube.deploy`
 
## Update

`git pull`

`pip install ./numericube.deploy`

## Use

Numericube.deploy provides some usefull fabric method for deploying git projet based on remote host

1. fab -H <host> deploy
    
    * Check if your project is deployable (ie, no pdb, everything is pushed on git)
    
    * Create a new tag base on your branch. New tag looks like vYYYYMMDD[a-z]_<name_ofyour_branch>
    
    
2. fab -H <host> release

   * Get the remote tag deployed on remote host
   
   * If no tag -> bootstrap your remote machine (see config for default pkg to be installed)
   
   * Else give you a review about previous versions installed on remote host
   
   * Call your provisionner on remote host (salt or ansible) and deploy your app
   
   * If everthing is ok, update git issue according to your git log.
   
3. fab -H <host> update_issues:git_previous_tag=<previous_tag>,git_release_tag=<release_tag>

  * Update git issue on tagging them by <host> to say that issue is deployed on <host>
  
4. fab latest_release

  * Return the latest release in your branch
  
5. fab -H <host> test

  * Test if remote machine is ready for deploy
  
6. fab get_git_token

  * tool for generate a git token that used for updating your git issues.


## Configure your project for numericube.deploy

  1. [Create deploy key in your git repository](https://developer.github.com/guides/managing-deploy-keys/#deploy-keys)
      We use this for deploying your application in remote host

  2. Generate a config file with generate_config utility
     `$ cd <project_directory>` 
     `$ generate_config` 

     And answers to questions

## Can I extends numericube.deploy ?
 
 Yes ! It is design for this
 
 Add simply a new method in your class (example a custom bootstrap method for your project)
 
 You can override method if you want.
