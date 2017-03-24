#################
OSX flat packages
#################

OSX flat packages are single installer files with ``.pkg`` file extensions.

They appear to have originated with OSX 10.5.  You can't install these files
on OSX < 10.5.

The previous packaging formats were *bundles* rather than single files:

bundle
    A structured directory hierarchy that stores files in a way that
    facilitates their retrieval (see glossary in the `software delivery legacy
    guide`_)

See :doc:`legacy_package_redux` for details.

As far as I know there is no Apple document describing the flat package
format.

You may find these other pages useful as background:

* A `MacTech flat package article`_;
* An introduction to the `flat package format`_;
* A guide on `unpacking flat packages`_ manually;
* A comprehensive `stackoverflow package building answer`_.

************************
Flat packages in general
************************

Flat packages are ``xar`` archives (see the ``xar`` man page).

To see the contents of a flat package, the most convenient command is
``pkgutil --expand``, as in::

    pkgutil --expand my.pkg an_output_dir

This will unpack product archive (meta-packages) and their component packages,
and allows you to futz with the directory contents in ``an_output_dir`` before
reconstituting the package with::

    pkgutil --flatten an_output_dir my.pkg

On OSX, ``tar`` will unpack xar archives, and will automatically detect that
the archive is in xar format with ``tar xf my.pkg``, if you really want to do
the unpacking without ``pkgutil``.

***********************
Different package types
***********************

Flat packages can be of type:

* *product archive* |--| a meta-package format containing one or more
  *component packages* with an XML file specifying the behavior of the
  installer, including system and volume requirement checks giving informative
  error messages. See the ``productbuild`` man page for more detail.
* *component package* |--| an installer to install one component. Generally
  included as part of a *product archive* but can be used as an installer in
  its own right.  A component package installer cannot control the behavior of
  the installer, but can abort the install or raise a post-install error
  via ``preinstall`` and ``postinstall`` scripts.

*******************
Component installer
*******************

A component installer goes through these stages:

#. Runs ``preinstall`` script if present.  An exit code other than zero aborts
   the installation.
#. Writes payload to one or more locations on the target volume
#. Runs ``postinstall`` script if present.  An exit code other then zero gives
   an error message.

We start with some component packages that only have scripts and no payload,
to show how they work.

Component installer scripts
===========================

.. runblock::
    :hide:

    rm -rf pkg_examples
    sudo pkgutil --forget my.fake.pkg
    sudo pkgutil --forget com.apple.xcode.dsym.aprogram
    sudo pkgutil --forget com.apple.xcode.dsym.aprogram2
    sudo rm -rf /tmp/my_*.log /tmp/dir1 /tmp/dir2 /tmp/aprogram*.dSYM

.. runblock::

    mkdir pkg_examples
    cd pkg_examples
    mkdir scripts

.. pkgwrite::
    :language: bash

    # file: scripts/preinstall
    #!/bin/sh
    echo "Running preinstall" > /tmp/my_preinstall.log
    exit 0 # all good

.. pkgwrite::
    :language: bash

    # file: scripts/postinstall
    #!/bin/sh
    echo "Running postinstall" > /tmp/my_postinstall.log
    exit 0 # all good

The scripts need to be executable:

.. pkgrun::

    chmod u+x scripts/*

Each package needs a package *identifier* to identify it to the database of
installed packages on the target system.

You can list the recorded installed packages on target ``/`` with::

    pkgutil --pkgs /

Build the package with a fake identifier:

.. pkgrun::

    pkgbuild --nopayload --scripts scripts --identifier my.fake.pkg my_package.pkg

Install the package:

.. pkgrun::

    sudo installer -pkg my_package.pkg -target /

Check the scripts ran by looking for output:

.. pkgrun::

    cat /tmp/my_preinstall.log
    cat /tmp/my_postinstall.log

Exit code other than zero causes the installer to give an error message:

.. pkgwrite::
    :language: bash

    # file: scripts/postinstall
    #!/bin/sh
    exit 1 # not so good

.. pkgrun::
    :allow-fail:

    pkgbuild --nopayload --scripts scripts --identifier my.fake.pkg my_package.pkg
    sudo installer -pkg my_package.pkg -target /

Fixed if the script is not run:

.. pkgrun::

    rm scripts/postinstall
    pkgbuild --nopayload --scripts scripts --identifier my.fake.pkg my_package.pkg
    sudo installer -pkg my_package.pkg -target /

There are some useful environment variables available to the
``preinstall``, ``postinstall`` scripts:

.. pkgrun::

    # Get the default environment when not in preinstall
    sudo env > /tmp/my_sudo_envs.log

.. pkgwrite::
    :language: bash

    # file: scripts/preinstall
    #!/bin/sh
    env > /tmp/my_preinstall_envs.log
    echo "Positional arguments" $@ >> /tmp/my_preinstall_envs.log
    exit 0

.. pkgrun::

    chmod u+x scripts/preinstall
    pkgbuild --nopayload --scripts scripts --identifier my.fake.pkg my_package.pkg
    sudo installer -pkg my_package.pkg -target /

Here are the new environment variables inserted by the installer:

.. runblock::
    :allow-fail:

    diff /tmp/my_sudo_envs.log /tmp/my_preinstall_envs.log --old-line-format="" --unchanged-line-format=""

These appear to be a superset of the environment variables listed for the old
bundle installers at `install operations`_.

No payload, no receipt
----------------------

These "scripts only" installers have no payload, and write no package receipt
to the package database:

.. runblock::
    :allow-fail:

    pkgutil --pkgs / | grep my.fake.pkg

Payload
=======

A flat-package component installer can install one or more bundles to given
output locations on the target filesystem.

There are two ways of specifying payload with target location:

* Using a *destination root*, using ``--root`` flag to ``pkgbuild``.  This
  analyzes a given directory ``root-path`` taking this directory to represent
  the root ``/`` directory of the target system.  The installer will copy each
  directory at ``root-path`` to the target system at the same relative
  filesystem location.
* By individual bundle *component*, using ``--component`` flag to
  ``pkgbuild``.  Specify directories to copy, and give their output locations
  separately using the ``--install-location`` flag.

.. _destination-root:

Destination root
----------------

.. pkgrun::

    mkdir -p my_root/tmp/dir1 my_root/tmp/dir2
    echo "Interesting info" > my_root/tmp/dir1/file1
    echo "Compelling story" > my_root/tmp/dir2/file2
    tree -a my_root

.. pkgrun::

    pkgbuild --root my_root --identifier my.fake.pkg my_package.pkg

.. pkgrun::
    :hide:

    sudo rm -rf /tmp/dir1 /tmp/dir2 my_file

Do the install:

.. pkgrun::

    sudo installer -pkg my_package.pkg -target /

.. pkgrun::

    cat /tmp/dir1/file1
    cat /tmp/dir2/file2

This install did write a package receipt:

.. pkgrun::

    pkgutil --pkgs / | grep my.fake.pkg

.. _explicit-component:

Explicit component(s)
---------------------

We point to a bundle to install and (usually) specify the install location.

In this case the bundle must be a properly formed bundle of some sort.

I'll make a debug symbols bundle by doing a tiny compilation with clang:

.. pkgrun::

    echo "int main(int argc, char** argv) { }" > aprogram.c
    clang -g aprogram.c -o aprogram
    tree aprogram.dSYM

.. pkgrun::
    :hide:

    sudo rm -rf /tmp/aprogram.dSYM /tmp/aprogram2.dSYM

Build, install the package:

.. pkgrun::

    pkgbuild --component aprogram.dSYM --install-location /tmp my_package.pkg

.. pkgrun::

    sudo installer -pkg my_package.pkg -target /

The installer has written the expected output files:

.. pkgrun::

    tree /tmp/aprogram.dSYM

You can add more than one bundle to a single component installer.

Here I make another bundle with a different name:

.. pkgrun::

    echo "int main(int argc, char** argv) { }" > aprogram2.c
    clang -g aprogram2.c -o aprogram2
    tree aprogram2.dSYM

When you add more than one component, you need to give a package identifier,
because ``pkgbuild`` will not know which component to get an identifier from.

.. pkgrun::

    pkgbuild --component aprogram.dSYM --install-location /tmp \
        --component aprogram2.dSYM --install-location /tmp \
        --identifier my.fake.pkg \
        my_package.pkg

.. pkgrun::

    sudo installer -pkg my_package.pkg -target /

.. pkgrun::

    tree /tmp/aprogram.dSYM
    tree /tmp/aprogram2.dSYM

***************
Product archive
***************

Component packages give a very basic default install.

Product archives allow you to wrap one or more component installs with an
install configuration that includes:

* custom welcome, readme, license and conclusion screens;
* custom system requirement and volume requirement checks with informative
  error messages using javascript code;
* ability to customize choices of component packages to install using
  javascript code.

An XML file named ``Distribution`` specifies these options (see `distribution
definition file`_).

Building product archives with ``productarchive``
=================================================

``productarchive`` has five modes of action:

Archive for "in-app" content
----------------------------

This appears to be something to do with the App Store.  Use the ``--content``
flag for this one.

Archive from destination root
-----------------------------

Build an archive from a directory where the paths of the files relative to the
``--root`` directory give the output install location on the target volume
(see :ref:`destination-root`).

.. pkgrun::

    productbuild --root my_root my_archive.pkg

Archive from component bundle(s) or package(s)
----------------------------------------------

Build a product archive from one or more components by passing:

* bundle path(s) with one or more uses of the ``--component`` flag (see
  :ref:`explicit-component`) and / or;
* package paths(s) with one or more uses of the ``--package`` flag.

Build product archive with two component bundles:

.. pkgrun::

    productbuild --component aprogram.dSYM /tmp --component aprogram2.dSYM /tmp my_archive.pkg

Make bundles into component packages:

.. pkgrun::

    pkgbuild --component aprogram.dSYM --install-location /tmp aprogram.pkg
    pkgbuild --component aprogram2.dSYM --install-location /tmp aprogram2.pkg

Build product archives from the component packages:

.. pkgrun::

    productbuild --package aprogram.pkg --package aprogram2.pkg my_archive.pkg

Build a ``Distribution`` file from component bundle(s) / packages(s)
--------------------------------------------------------------------

This builds a template ``Distribution`` XML file by analyzing one or more
components in the form of bundles or ``.pkg`` files.  Use the ``--synthesize``
flag.

Analyze two component bundles to give a ``Distribution`` file:

.. pkgrun::

    productbuild --synthesize --component aprogram.dSYM --component aprogram2.dSYM Distribution-1

Analyze two component packages to give a ``Distribution`` file:

.. pkgrun::

    productbuild --synthesize --package aprogram.pkg --package aprogram2.pkg Distribution-2

.. pkgrun::

    cat Distribution-2

Archive from ``Distribution`` file
----------------------------------

Build a product archive from a pre-existing ``Distribution`` file, using the
``--distribution`` flag.  The ``Distribution`` file refers to pre-existing
component ``.pkg`` files.  If these are not in the current directory, you can
give paths to find ``.pkg`` files with the ``--package-path`` flag.

.. pkgrun::

    productbuild --distribution Distribution-2 my_archive.pkg

*************************************
Customizing the ``Distribution`` file
*************************************

See: `distribution definition file`_ and `installer javascript reference`_.

Adding system and volume checks
===============================

.. pkgwrite::
    :language: xml

    # file: distro_check.xml
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <installer-gui-script minSpecVersion="1">
        <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        <choices-outline>
            <line choice="default">
                <line choice="com.apple.xcode.dsym.aprogram"/>
                <line choice="com.apple.xcode.dsym.aprogram2"/>
            </line>
        </choices-outline>
        <choice id="default"/>
        <choice id="com.apple.xcode.dsym.aprogram" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram" version="1.0.0" onConclusion="none">aprogram.pkg</pkg-ref>
        <choice id="com.apple.xcode.dsym.aprogram2" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2" version="1.0.0" onConclusion="none">aprogram2.pkg</pkg-ref>
        <installation-check script="installation_check()"/>
        <volume-check script="volume_check()"/>
        <script><![CDATA[

    function installation_check () {
        // Check 64 bit
        if (! system.sysctl('hw.cpu64bit_capable')) {
            // need to set error type
            my.result.type = "Fatal"
            my.result.message = "Installer needs 64 bit"
            return false
        }
        return true
    }

    function volume_check () {
        // check installed file exists
        log_file = my.target.mountpoint + 'tmp/my_postinstall.log'
        if (! system.files.fileExistsAtPath(log_file)) {
            // need to set error type
            my.result.type = "Fatal"
            my.result.message = "No my_postinstall file on volume"
            return false
        }
        return true
    }

        ]]></script>
    </installer-gui-script>

.. pkgrun::

    productbuild --distribution distro_check.xml my_archive.pkg

.. pkgrun::

    sudo installer -pkg my_archive.pkg -target /

Now make the volume check fail:

.. pkgrun::
    :allow-fail:

    sudo rm /tmp/my_postinstall.log
    sudo installer -pkg my_archive.pkg -target /

The volume check gets run on every candidate volume; each volume that passes
the check is eligible for the install.

Debugging ``Distribution`` javascript with ``system.log``
=========================================================

Getting the javascript right can be tricky because it is running in a highly
specific environment.  ``system.log()`` can help.

.. pkgwrite::
    :language: xml

    # file: distro_debug.xml
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <installer-gui-script minSpecVersion="1">
        <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        <choices-outline>
            <line choice="default">
                <line choice="com.apple.xcode.dsym.aprogram"/>
                <line choice="com.apple.xcode.dsym.aprogram2"/>
            </line>
        </choices-outline>
        <choice id="default"/>
        <choice id="com.apple.xcode.dsym.aprogram" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram" version="1.0.0" onConclusion="none">aprogram.pkg</pkg-ref>
        <choice id="com.apple.xcode.dsym.aprogram2" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2" version="1.0.0" onConclusion="none">aprogram2.pkg</pkg-ref>
        <installation-check script="installation_check()"/>
        <script><![CDATA[

    function installation_check () {
        // Some debug prints
        system.log('my: ' + system.propertiesOf(my))
        system.log('system: ' + system.propertiesOf(system))
        system.log('system.applications: ' +
            system.propertiesOf(system.applications))
        return true
    }

        ]]></script>
    </installer-gui-script>

.. pkgrun::

    productbuild --distribution distro_debug.xml my_archive.pkg

Use the ``-dumplog`` flag to the installer to see the log.

.. pkgrun::

    sudo installer -dumplog -pkg my_archive.pkg -target /

Adding custom script checks
===========================

You can add custom executable scripts or binaries to run via the javascript
functions such as the volume check and the system check.

You first have to enable the ``allow-external-scripts`` option in the
Distribution file XML::

    <options allow-external-scripts="yes"/>

This will cause the installer GUI to ask if you want to allow an external
script to check if the software can be installed.

You can then call external programs via the javascript ``system.run()``
function.  The programs you call with ``system.run`` either need to be on the
system PATH that the installer uses, or provided in the installer, usually via
the ``--scripts`` flag to ``productbuild``.  Here's an example of a command
already on the path:

.. pkgwrite::
    :language: xml

    # file: distro_system_run.xml
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <installer-gui-script minSpecVersion="1">
        <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        <options allow-external-scripts="yes"/>
        <choices-outline>
            <line choice="default">
                <line choice="com.apple.xcode.dsym.aprogram"/>
                <line choice="com.apple.xcode.dsym.aprogram2"/>
            </line>
        </choices-outline>
        <choice id="default"/>
        <choice id="com.apple.xcode.dsym.aprogram" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram" version="1.0.0" onConclusion="none">aprogram.pkg</pkg-ref>
        <choice id="com.apple.xcode.dsym.aprogram2" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2" version="1.0.0" onConclusion="none">aprogram2.pkg</pkg-ref>
        <installation-check script="installation_check()"/>
        <script><![CDATA[

    function installation_check () {
        // Run some sh code
        exit_code = system.run('/bin/sh', '-c',
            'echo "Command ran" > /tmp/my_system_run.log; exit 1')
        if (exit_code != 0) {
            // need to set error type
            my.result.type = "Fatal"
            my.result.message = "Test function failed by design"
            return false
        }
        return true
    }

        ]]></script>
    </installer-gui-script>

.. pkgrun::

    productbuild --distribution distro_system_run.xml my_archive.pkg

.. pkgrun::
    :allow-fail:

    sudo installer -pkg my_archive.pkg -target /

Check the script ran:

.. pkgrun::

    cat /tmp/my_system_run.log

Here's an example of a custom script:

.. pkgwrite::
    :language: xml

    # file: distro_custom_run.xml
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <installer-gui-script minSpecVersion="1">
        <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        <options allow-external-scripts="yes"/>
        <choices-outline>
            <line choice="default">
                <line choice="com.apple.xcode.dsym.aprogram"/>
                <line choice="com.apple.xcode.dsym.aprogram2"/>
            </line>
        </choices-outline>
        <choice id="default"/>
        <choice id="com.apple.xcode.dsym.aprogram" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram" version="1.0.0" onConclusion="none">aprogram.pkg</pkg-ref>
        <choice id="com.apple.xcode.dsym.aprogram2" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2" version="1.0.0" onConclusion="none">aprogram2.pkg</pkg-ref>
        <installation-check script="installation_check()"/>
        <script><![CDATA[

    function installation_check () {
        // Run a custom script
        exit_code = system.run('my_test_cmd.sh', 'args', 'I', 'passed');
        if (exit_code != 0) {
            // need to set error type
            my.result.type = "Fatal"
            my.result.message = "Test function failed by design"
            return false
        }
        return true
    }

        ]]></script>
    </installer-gui-script>

Make a directory to contain the test script:

.. pkgrun::

    mkdir archive_scripts

Use test script to look for any interesting environment variables available to
the custom script:

.. pkgwrite::
    :language: bash

    # file: archive_scripts/my_test_cmd.sh
    #!/bin/sh
    env > /tmp/my_custom_envs.log
    echo "Positional arguments" \$@ >> /tmp/my_custom_envs.log
    exit 2

The script must be executable:

.. pkgrun::

    chmod u+x archive_scripts/my_test_cmd.sh

Build the product archive with ``--scripts`` flag:

.. pkgrun::

    productbuild --distribution distro_custom_run.xml --scripts archive_scripts my_archive.pkg

.. pkgrun::
    :allow-fail:

    sudo installer -pkg my_archive.pkg -target /

Check the environment variables available to the custom script.  We already
have ``/tmp/my_sudo_envs.log`` with the standard environment variables
available as root, so look for the difference:

.. pkgrun::
    :allow-fail:

    diff /tmp/my_sudo_envs.log /tmp/my_custom_envs.log --old-line-format="" --unchanged-line-format=""

There do not seem to be any environment variables to tell us where the
installer ``.pkg`` file is.  Here we can work out which volume the installer
is installing to with the ``SUDO_COMMAND`` variable, but this will only work
for command line installs - the installer GUI does not set this variable.

Customizing the installer pages
===============================

See `distribution definition file`_ for details.

You can customize these pages:

* Welcome (``<welcome ... />`` element)
* Readme  (``<readme ... />``)
* License (``<license ... />``)
* Conclusion (``<conclusion ... />``)

To do this, you specify the filename containing the custom text, and the
format of the file.  For example::

    <welcome file="welcome.html" mime-type="text/html"/>

The file should be in the ``Resources/<language>.lproj`` directory of the
installer ``.pkg``, where ``<language>`` is a language like "English",
"French" or "Spanish", or shorthand for these such as "en", "fr", "es".  Can
you can provide a ``Resources`` directory with the ``--resources`` flag to
``productbuild``.

.. pkgrun::

    mkdir -p my_resources/English.lproj

.. pkgwrite::
    :language: html

    # file: my_resources/English.lproj/welcome.html
    <html lang="en">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
        <title>Install my_archive </title>
    </head>
    <body>
    <font face="Helvetica">
    <b>Welcome to the <i>my_archive</i> installer</b>
    <p>
    This installer will install <i>my_archive</i> on your computer.
    </font>
    </ul>
    </body>
    </html>

.. pkgwrite::
    :language: xml

    # file: distro_welcome.xml
    <?xml version="1.0" encoding="utf-8" standalone="no"?>
    <installer-gui-script minSpecVersion="1">
        <welcome file="welcome.html" mime-type="text/html"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        <choices-outline>
            <line choice="default">
                <line choice="com.apple.xcode.dsym.aprogram"/>
                <line choice="com.apple.xcode.dsym.aprogram2"/>
            </line>
        </choices-outline>
        <choice id="default"/>
        <choice id="com.apple.xcode.dsym.aprogram" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram" version="1.0.0" onConclusion="none">aprogram.pkg</pkg-ref>
        <choice id="com.apple.xcode.dsym.aprogram2" visible="false">
            <pkg-ref id="com.apple.xcode.dsym.aprogram2"/>
        </choice>
        <pkg-ref id="com.apple.xcode.dsym.aprogram2" version="1.0.0" onConclusion="none">aprogram2.pkg</pkg-ref>
    </installer-gui-script>

We use the ``--resources`` flag to add the resources directory:

.. pkgrun::

    productbuild --distribution distro_welcome.xml --resources my_resources my_archive.pkg

The welcome won't show up in the command line install, so you need to run this
installer via the GUI to see the new text.

I used an HTML file here, and that works as expected, for me at least.  There
are many installers that use ``.rtf`` files instead of HTML, but I heard a
rumor that ``productbuild`` does not deal with these correctly. If you want to
use rich text format files with ``productbuild``, you might have to do some
post-processing of your installer with |--| ``pkgutil --expand my_archive.pkg
out_dir``; (futz); ``pkgutil --flatten out_dir my_archive.pkg``.

.. include:: links_names.inc
