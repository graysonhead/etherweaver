Writing Plugins
===============

This is the best place to start if you plan on building a plugin.

There are a few different archetypes of each set function:

#TODO Examine archetypes

All methods must have execute and it must default to True. IF execute is true, run and apply the command immediately
Otherwise just return the line(s) needed to run the command

If you plan on implementing a method in the future, please override that module and raise a NotImplemented exception.

The plugin you implement *MUST* accept all of the arguments present in the skeleton class (documented below).

Plugin Class Structure
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: etherweaver.plugins.plugin_class.NetWeaverPlugin
   :members:

