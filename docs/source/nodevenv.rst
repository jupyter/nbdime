Setting up a virtualenv with Node.js
------------------------------------

The following steps will: create a virtualenv, named ``myenv``, in the current
directory; activate the virtualenv; and install npm inside the virtualenv
using :command:`nodeenv`::

    python -m venv myenv
    source myenv/bin/activate
    pip install nodeenv
    nodeenv -p

With this environment active, you can now install nbdime and its
dependencies using :command:`pip`.

For example with Python 3.5, the steps with output are::

    $ python -m venv myenv
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
