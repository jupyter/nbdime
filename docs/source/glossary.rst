Glossary
========

.. glossary::

   diff object
      A diff object represents the difference ``B-A`` between two objects, ``A`` and
      ``B``, as a list of operations (ops) to apply to ``A`` to obtain ``B``.

   merge decision
      An object describing a part of the merge operation between two objects
      with a common base. Contains both the information about local and remote
      changes, and the decision taken to resolve the merge.

   JSONPatch
      JSON Patch defines a JSON document structure for expressing a
      sequence of operations to apply to a JavaScript Object Notation
      (JSON) document; it is suitable for use with the ``HTTP PATCH`` method. See
      `RFC 6902 JavaScript Object Notation (JSON) Patch <https://tools.ietf.org/html/rfc6902>`_.