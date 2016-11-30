# REST API draft for nbdime server v0.1

The following is a **draft** of the REST API for nbdime. It is not yet frozen
but is guided on preliminary work and likely close to the final
result. It is also not implemented in this form yet.

The Python package, commandline, and web API should cover the same
functionality using the same names but different methods of passing
input/output data.  Thus consider the request to be the input
arguments and response to be the output arguments for all APIs.


## Definitions

`json_*` always a JSON object

`json_notebook` a full Jupyter notebook

`json_diff_args` arguments to control nbdiff behaviour

`json_merge_args` arguments to control nbmerge behaviour

`json_diff_object` diff result in nbdime diff format

`**json_merge_object` merge result in nbdime merge format


## /diff

Compute diff of two notebooks provided in full JSON format.

Request:

    {
      "base":   json_notebook,
      "remote": json_notebook,
      "args": json_diff_args
    }

Response:

    {
      "diff": json_diff_object
    }


## /merge

Compute merge of three notebooks provided in full JSON format.

Request:

    {
      "base":   json_notebook,
      "local":  json_notebook,
      "remote": json_notebook,
      "args": json_merge_args
    }

Response:

    {
      "merged": json_notebook,
      "localconflicts": json_diff_object,
      "remoteconflicts": json_diff_object,
    }


## /localdiff

Compute diff of notebooks known to the server by name.

Request:

    {
      "base":   "filename.ipynb",
      "remote": "filename.ipynb",
      "args": json_diff_args
    }

Response:

    {
      "base": json_notebook,
      "diff": json_diff_object
    }


## /localmerge

Compute merge of notebooks known to the server by name.

Request:

    {
      "base":   "filename.ipynb",
      "local":  "filename.ipynb",
      "remote": "filename.ipynb",
      "args": json_merge_args
    }

Response:

    {
      "merged": json_notebook,
      "localconflicts": json_diff_object,
      "remoteconflicts": json_diff_object,
    }
