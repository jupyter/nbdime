========
REST API
========

The following is a preliminary REST API for nbdime. It is not yet frozen
but is guided on preliminary work and likely close to the final
result.

The Python package, commandline, and web API should cover the same
functionality using the same names but different methods of passing
input/output data. Thus consider the request to be the input
arguments and response to be the output arguments for all APIs.



Definitions
------------

`json_*` : always a JSON object

`json_notebook` : a full Jupyter notebook

`json_diff_object` : diff result in nbdime diff format as specified in :doc:`diffing`

`json_merge_decisions` : merge decisions as specified in :doc:`merging`



/api/diff
---------

Compute diff of two notebooks provided as filenames local
to the server working directory, and/or as URLs.

Request::

    {
      "base":   "filename.ipynb" | "http://your-domain/url/path",
      "remote": "filename.ipynb" | "http://your-domain/url/path"
    }

Response::

    {
      "base": json_notebook,
      "diff": json_diff_object
    }


/api/merge
----------

Compute merge of three notebooks provided as filenames local
to the server working directory, and/or as URLs.

Request::

    {
      "base":   "filename.ipynb" | "http://your-domain/url/path",
      "local":  "filename.ipynb" | "http://your-domain/url/path",
      "remote": "filename.ipynb" | "http://your-domain/url/path"
    }

Response::

    {
      "base": json_notebook,
      "merge_decisions": json_merge_decisions
    }
