import unittest
from netweaver.core_classes import appliance

suite = unittest.TestLoader().loadTestsFromModule(appliance)
unittest.TextTestRunner(verbosity=2).run(suite)