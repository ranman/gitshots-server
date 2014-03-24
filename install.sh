#!/bin/sh
bin=~/bin
hooks=~/.git_template/hooks

echo "Creating git_template dir"
mkdir -p ~/.git_template/hooks
git config --global init.templatedir '~/.git_template/'
echo "Putting post-commit.py in bin"
mkdir -p ~/bin
curl https://raw.githubusercontent.com/ranman/gitshots/master/post-commit.py > ~/bin/post-commit.py
echo "Creating post-commit hook"
cat << EOF > ~/.git_template/hooks/post-commit
#!/bin/sh
/usr/bin/python2.7 ~/bin/post-commit.py
EOF
chmod +x ~/.git_template/hooks/post-commit
echo "Installing requests dependency, if this fails fix your python or use sudo"
pip install requests
echo "Installing imagesnap dependency"
brew install imagesnap

echo "\n\nNow just run git init in any repo you want to use the commit hook in!"
