# Gitshots — remember every commit



## Setting up your own Gitshots server

Setting up your own Gitshots server is as easy as deploying to Heroku (just copy and paste these commands).

    git clone https://github.com/ranman/gitshots
    heroku create
    heroku addons:add mongohq:sandbox
    git push heroku master

If you don't want to set up your own Gitshots server, feel free to use [ranman's](http://gitshots.ranman.org) (it's the default).

If you'd rather not post to Gitshots in general, just record to disk, set the GITSHOTS_SERVER_URL to `False`

## Taking a gitshot on every commit

With your Gitshots server setup, you need to configure your computer to take gitshots.

First, add the following line to your `.bash_profile` or `.bashrc`. If you don't add this line with your server URL, your gitshots will be posted to [ranman's gitshot server](http://gitshots.ranman.org).

    export GITSHOTS_SERVER_URL=<your gitshots server url>

Next, you'll need to make sure you have `python2.7` and the `requests` library:

    pip install requests

Next, you'll need to make sure you have `imagesnap`, on OSX you can easily install it with [homebrew](http://mxcl.github.io/homebrew/):

    brew install imagesnap

Next, in any repository that you want gitshots, you need to add the following line to your `.git/hooks/post-commit` file (if you don't have one, create one):

    /usr/bin/env python2.7 PATH_TO_GITSHOTS_REPO/post-commit.py

An easy way to ensure your gitshots take for every new repository you create in the future is to add the following file at `/usr/share/git-core/templates/hooks/post-commit` or `/usr/local/share/git-core/templates/hooks/post-commit` depending on your installation of git.

    #!/bin/sh

    # takes a gitshot on every commit
    /usr/bin/env python2.7 PATH_TO_GITSHOTS_REPO/post-commit.py

Be sure to mark both of these files as executable: `chmod +x post-commit`
