import unittest
from etherweaver.core_classes import appliance

suite = unittest.TestLoader().loadTestsFromModule(appliance)
unittest.TextTestRunner(verbosity=2).run(suite)