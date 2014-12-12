##############################
Serving MathJax locally on OSX
##############################

I'm often in Cuba with no or very slow internet.

I have a local copy of MathJax that I use for reading and writing IPython
notebooks.

Now I want to read Sphinx pages that use MathJax markup.

I worked off these two pages, both by Neil Gee:

* `Installation guide for Apache etc
  <http://coolestguidesontheplanet.com/get-apache-mysql-php-phpmyadmin-working-osx-10-9-mavericks/>`_
  on OSX 10.9;
* `Using virtualhosts on OSX
  <http://coolestguidesontheplanet.com/set-virtual-hosts-apache-mac-osx-10-9-mavericks-osx-10-8-mountain-lion/>`_

***
Map
***

* Link local copy of MathJax into ``~/Sites/cdn.mathjax.org/mathjax/latest``;
* Enable apache serving from my ``~/Sites`` user directories;
* Enable apache virtualhost for ``cdn.mathjax.org`` domain;
* Redirect IP traffic for ``cdn.mathjax.org`` to localhost;
* Restart apache.

*******
Details
*******

Linking local copy of MathJax
=============================

The page I wanted to serve is expecting this URL:
``http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML``.

My task is to set up a redirect so that my own machine serves this URL.

Luckily OSX comes shipped with a version of the ``apache`` web server.

I have a local copy of MathJax, stored in ``~/stable_trees/mathjax``.  This
directory contains ``MathJax.js``.

OSX ``apache`` expects to serve user pages from ``~/Sites``.  So, the linking
step is::

    cd
    mkdir -p Sites/cdn.mathjax.org/mathjax
    ln -s ~/stable_trees/mathjax Sites/cdn.mathjax.org/mathjax/latest

Enable apache serving from ``~/Sites`` directories
==================================================

Replace ``my_user`` with your login username in the following::

    sudo bash
    cd /etc/apache2/users
    MY_USERNAME=my_user
    cat > ${MY_USERNAME}.conf << EOF
    <Directory "/Users/${MY_USERNAME}/Sites/">
    Options Indexes MultiViews FollowSymLinks
    AllowOverride None
    Order allow,deny
    Allow from all
    </Directory>
    EOF

Now start apache::

    sudo apachectl start

You now should be able to read
``http://localhost/~my_user/cdn.mathjax.org/mathjax/latest`` in your browser
(where you need to replace ``my_user`` in the URL with your login username).

Enable apache virtualhost for mathjax directory
===============================================

(As root) edit ``/etc/apache2/httpd.conf``.

Uncomment the line ``Include /private/etc/apache2/extra/httpd-vhosts.conf``
and save.

Edit ``/etc/apache2/extra/httpd-vhosts.conf``.

Add the following at the end::

    <VirtualHost *:80>
        ServerName cdn.mathjax.org
        DocumentRoot "/Users/my_user/Sites/cdn.mathjax.org"
        ErrorLog "/private/var/log/apache2/mathjax.org-error_log"
        CustomLog "/private/var/log/apache2/mathjax.org-access_log" common
        ServerAdmin your.name@your.address.com
        <Directory "/Users/my_user/Sites/cdn.mathjax.org">
            Options Indexes FollowSymLinks
            AllowOverride All
            Order allow,deny
            Allow from all
        </Directory>
    </VirtualHost>

where you replace ``my_user`` with your login username.

Note the ``FollowSymLinks`` option |--| we need this because the directory we
want to serve is in fact a symbolic link.

Redirect IP traffic for ``cdn.mathjax.org`` to localhost
========================================================

(As root), edit ``/etc/hosts`` and add the following line::

    127.0.0.1 cdn.mathjax.org

Restart apache
==============

::

    sudo apachectl restart

You should now be able to disconnect your internet connection but still get a
directory listing in your browser for http://cdn.mathjax.org/mathjax/latest/.
You should also be able to get rendered MathJax pages offline and at blazing
speed.

.. include:: links_names.inc
