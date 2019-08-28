paws.core.operations.SPEC package
===============================================

Submodules
----------

paws.core.operations.SPEC.LoadSpecFile module
------------------------------------------------------------

.. automodule:: paws.core.operations.SPEC.LoadSpecFile
    :members:
    :undoc-members:
    :show-inheritance:

**Inputs**

* file_path: full path to the SPEC file to be loaded

**Outputs**

* spec_dict: dictionary with the following keys:
  * header: top level information from the SPEC file
  * S\#: scan numbers are used as keys to access dictionary with two keys:
  *  scan: pandas DataFrame which holds the scan itself
  *  meta: associated scan meta information

Module contents
---------------

.. automodule:: paws.core.operations.SPEC
    :members:
    :undoc-members:
    :show-inheritance: 