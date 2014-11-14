#! /bin/bash

export PACKAGE=YetAnotherCodeSearch
export ST_PACKAGE_DIR=$HOME/.config/sublime-text-3/Packages

if [ -z $(which subl) ]; then
  echo "Installing Sublime Text 3"
  sudo add-apt-repository ppa:webupd8team/sublime-text-3 -y
  sudo apt-get update
  sudo apt-get install sublime-text-installer -y
fi

if [ ! -d $ST_PACKAGE_DIR ]; then
    echo "Creating the Sublime package directory"
    mkdir -p $ST_PACKAGE_DIR
fi

if [ ! -d $ST_PACKAGE_DIR/$PACKAGE ]; then
    echo "Symlinking the package to the Sublime package directory"
    ln -s $PWD $ST_PACKAGE_DIR/$PACKAGE
fi

if [ ! -d $ST_PACKAGE_DIR/UnitTesting ]; then
    echo "Downloading latest UnitTesting release"
    # for stability, you may consider a fixed version of UnitTesting, eg TAG=0.1.4
    TAG=$(git ls-remote --tags https://github.com/randy3k/UnitTesting | sed 's|.*/\([^/]*$\)|\1|' | sort -r | head -1)
    git clone --branch $TAG https://github.com/randy3k/UnitTesting $ST_PACKAGE_DIR/UnitTesting
fi
