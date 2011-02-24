import unittest
import os


class ConfigTests(unittest.TestCase):
    """ Test the config is generated normally """

    def setUp(self):
        self.location = os.path.dirname(__file__)
        self.tracini = os.path.join(self.location, 'var', 'trac', 'conf', 'trac.ini')
        self.basetracini = os.path.join(self.location, 'var', 'trac', 'conf', 'base_trac.ini')
        pass

    def testBaseConfigExists(self):
        """ Check that the base config file is created """
        path_to_check = self.basetracini 
        result = os.path.exists(path_to_check)
        self.assertTrue(result, "base_trac.ini not created")

    def testTracIniCreated(self):
       """ Check that the base config file is created """
       path_to_check = self.tracini
       result = os.path.exists(path_to_check)
       self.assertTrue(result, "Trac ini not created") 

    def testContentsTracIni(self):
        """  Check that we haven't got the default config and we've got our generated one """
        path_to_check = self.tracini
        tracini = open(path_to_check).read()

        # check it's the right length
        split = tracini.split('\n')
        self.assertTrue(len(split) == 5, "trac.ini is the wrong length")

        file_split = split[2].split(' ')
        self.assertTrue(file_split[2] == self.basetracini)