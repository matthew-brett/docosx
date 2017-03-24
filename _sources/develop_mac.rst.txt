#################
Developing on mac
#################

Sketch of the steps to get up and running on a Mac to make binary releases for
Python packages.  This is my personal setup.

Here's a remarkably helpful short page on distinctive things about doing
system and development work with Mac OSX binaries :
http://www.tribler.org/trac/wiki/MacBinaries

***********
Basic setup
***********

* Xcode_, obviously;
* git_ - see the `github osx installation`_;
* editor.  I like vim_ - via MacVim_;
* consider installing homebrew_;
* For every Python version you want to support, download the "Mac installer
  disk image" ``dmg`` or ``pkg`` installer file via the links from the
  `Python.org releases`_.  Run the installation.
* Check in your ``~/.bash_profile`` to see what version of Python will reach
  your path first.  Adapt to taste.  Python.org installs go in directories
  like ``/Library/Frameworks/Python.framework/Versions/2.7``. You need this
  directory with ``/bin`` appended on your path.
* Install personal setup.  This is what that looks like for me (I store my set
  up on github to make it easier to move between computers)::

    git clone https://github.com/matthew-brett/myconfig.git
    cd myconfig
    make dotfiles
    cd ..

  I then edit ``~/.bash_profile`` to add the commented lines at the top of
  your new ``~/.bash_personal`` file.  Finally I set up my configuration of
  ``vim``::

    git clone https://github.com/matthew-brett/myvim.git
    cd myvim
    make
    make links

* For your favorite Python version, install virtualenv_, and
  virtualenvwrapper_
* If you are using my config (above), you probably want my default environment
  cleanup for virtualenvs::

    cd myconfig
    make virtualenvs

* Make some good virtualenvs, with commands like::

    mkvirtualenv --python=/Library/Frameworks/Python.framework/Versions/2.7/bin/python python27
    mkvirtualenv --python=/Library/Frameworks/Python.framework/Versions/3.6/bin/python3 python36

* For each virtualenv you're going to use (to taste)::

    workon python36
    pip install ipython

  Maybe also install useful development tools::

    pip install cython

.. include:: links_names.inc
