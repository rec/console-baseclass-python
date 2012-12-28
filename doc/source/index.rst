.. console_baseclass_python documentation master file, created by
   sphinx-quickstart on Sun Dec 16 22:12:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Python Console Baseclass documentation
======================================

.. module:: console
.. note::
    Module should be imported by *import console* to retrieve flags defined in console.py

Console
+++++++
.. autoclass:: Console
    :members: 


Custom Exceptions
+++++++++++++++++
.. autoclass:: CallError
    :members:
.. autoclass:: InputError
    :members:

Constant Flags
++++++++++++++
Flags for the :class:`Display_Information` class. Used to indicate the log level of each of
the information relay methods.
    0. **DI_IGNORE**
    1. **DI_STDOUT**
    2. **DI_LOG**
    3. **DI_STDOUT_LOG**

Flags used to initiate the in-program console :meth:`Console.console_start` which determines
the :class:`Display_Information` settings.
    0. **DI_CONSOLE_IGNORE** - all settings will be set to **DI_IGNORE**
    1. **DI_CONSOLE_INHERIT** - all settings will be inherited with the settings present in
       :class:`Console`

Flags used internally to represent expected input type from a flag
    0. **FLAG_INPUT_IGNORE**
    1. **FLAG_INPUT_STR**
    2. **FLAG_INPUT_INT**
    3. **FLAG_INPUT_FLOAT**

Command
+++++++

.. autoclass:: Command
    :members:

Display information
===================
Print information flow throughout your program to either the user and/or logfile.

.. automodule:: console
    :members: Display_Information


.. toctree::
   :maxdepth: 2



