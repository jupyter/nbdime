=========
Use cases
=========

Use cases for nbdime are envisioned to be mainly in the categories
of a merge command for version control integration and
diff command for inspecting changes and automated regression
testing. At the core of nbdime is the diff algorithms, which
must handle not only text in source cells but also a number of
data formats based on mime types in output cells.


Basic diffing use cases
-----------------------

While developing basic correct diffing is fairly
straightforward, there are still
some issues to discuss.

Other tasks (issues will be created for these):

  - Plugin framework for mime type specific diffing.

  - Diffing of common output types (png, svg, etc.)

  - Improve fundamental sequence diff algorithm.
    Current algorithm is based on a brute force
    O(N^2) longest common subsequence (LCS) algorithm. This
    will be rewritten in terms of a faster algorithm such
    as Myers O(ND) LCS based diff algorithm, optionally
    using Python's difflib for some use cases where it makes sense.


Version control use cases
-------------------------

Most commonly, cell source is the primary content,
and output can presumably be regenerated. Indeed, it
is not possible to guarantee that merged sources and
merged output is consistent or makes any kind of sense.

Some tasks:

  - Merge of output cell content is not planned.

  - Is it important to track source lines moving between cells?


Regression testing use cases
----------------------------

.. TODO:: Add text and description