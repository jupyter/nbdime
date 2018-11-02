Setting up a virtualenv with Node.js
------------------------------------

The following steps will: create a virtualenv, named ``myenv``, in the current
directory; activate the virtualenv; and install npm inside the virtualenv
using :command:`nodeenv`::

    python3 -m venv myenv          # For Python 2: python2 -m virtualenv myenv
    source myenv/bin/activate
    pip install nodeenv
    nodeenv -p

With this environment active, you can now install nbdime and its
dependencies using :command:`pip`.

For example with Python 3.5, the steps with output are::

    $ python3 -m venv myenv
    $ source myenv/bin/activate
    (myenv) $ pip install nodeenv
    Collecting nodeenv
      Downloading nodeenv-1.0.0.tar.gz
    Installing collected packages: nodeenv
      Running setup.py install for nodeenv ... done
    Successfully installed nodeenv-1.0.0
    (myenv) $ nodeenv -p
     * Install prebuilt node (7.2.0) ..... done.
     * Appending data to /Users/username/myenv/bin/activate
    (myenv) $

Using Python 2.7, the steps with output are (note: you may need to install
virtualenv as shown here)::

    $ python2 -m pip install virtualenv
    Collecting virtualenv
      Downloading virtualenv-15.1.0-py2.py3-none-any.whl (1.8MB)
        100% |████████████████████████████████| 1.8MB 600kB/s
    Installing collected packages: virtualenv
    Successfully installed virtualenv-15.1.0
    $ python2 -m virtualenv myenv
    New python executable in /Users/username/myenv/bin/python
    Installing setuptools, pip, wheel...done.
    $ source myenv/bin/activate
    (myenv) $ pip install nodeenv
    Collecting nodeenv
      Downloading nodeenv-1.0.0.tar.gz
    Installing collected packages: nodeenv
      Running setup.py install for nodeenv ... done
    Successfully installed nodeenv-1.0.0
    (myenv) $ nodeenv -p
     * Install prebuilt node (7.2.0) ..... done.
     * Appending data to /Users/username/myenv/bin/activate
    (myenv) $
