========================
Reference management CLI
========================

Concepts
========

Bibliography:
a set of citations stored in a ``bib`` file.

Master bibliography:
a bibliography (i.e., ``bib`` file) that contains all of your citations,
across all papers.

``refs`` file:
a file that tracks reference metadata.

Citekey:
a unique identifier for each reference.

Usage
=====

Add the citations from the passed bibliography
(or bibliographies) to the master bibliography.

.. code-block:: bash

   refs import BIBLIOGRAPHY...

Add a PDF file to the master bibliography.
The metadata of the file will be automatically determined;
if it cannot be determined,
you will be prompted to enter the missing information.
A citekey can optionally be specified;
if not specified, it will be generated as
``authoryear[letter]`` where ``[letter]`` is
a letter added to ensure uniqueness.

.. code-block:: bash

   refs add PDFFILE [CITEKEY] [BIBLIOGRAPHY]

Add one or more citations from the master bibliography
to the specified bibliography.

.. code-block:: bash

   refs add CITEKEY... BIBLIOGRAPHY

Remove one or more citations.
If a bibliography is specified,
the citation will be removed from the master bibliography.

.. code-block:: bash

   refs rm CITEKEY... [BIBLIOGRAPHY]

Sort one or more bibliographies by citekey.

.. code-block:: bash

   refs sort BIBLIOGRAPHY...

Output a bibliography in human-readable format.

.. code-block:: bash

   refs list BIBLIOGRAPHY
