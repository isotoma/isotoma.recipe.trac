import unittest
import os


class ConfigTests(unittest.TestCase):
    """ Test the config is generated normally """

    def setUp(self):
        self.location = os.path.dirname(__file__)
        self.tracini = os.path.join(self.location, 'var', 'trac', 'conf', 'trac.ini')
        self.basetracini = os.path.join(self.location, 'var', 'trac', 'conf', 'base_trac.ini')

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


class MetaInstanceTests(unittest.TestCase):
    """ Test that you can create multiple instances properly with the meta-mode """

    def setUp(self):
        self.location = os.path.dirname(__file__)
        self.basetracini = os.path.join(self.location, 'var', 'meta-trac', 'base_trac.ini')
        self.project_location = os.path.join(self.location, 'var', 'meta-trac')
        self.project_one_location = os.path.join(self.project_location, 'project1')
        self.project_two_location = os.path.join(self.project_location, 'project2')

    def testProjectsCreated(self):
        """ Check that the directories for the instances were created """
        result = os.path.exists(self.project_one_location)
        self.assertTrue(result)
        result_two = os.path.exists(self.project_two_location)
        self.assertTrue(result_two)
        
    def testProjectOneIniFiles(self):
        """  Check that we haven't got the default config and we've got our generated one """
        path_to_check = os.path.join(self.project_one_location, 'conf', 'trac.ini')
        tracini = open(path_to_check).read()

        # check it's the right length
        split = tracini.split('\n')
        self.assertTrue(len(split) == 12, "trac.ini is the wrong length")

        file_split = split[2].split(' ')
        self.assertTrue(file_split[2] == self.basetracini)
        
    def testProjectTwoIniFiles(self):
        """  Check that we haven't got the default config and we've got our generated one """
        path_to_check = os.path.join(self.project_two_location, 'conf', 'trac.ini')
        tracini = open(path_to_check).read()

        # check it's the right length
        split = tracini.split('\n')
        self.assertTrue(len(split) == 12, "trac.ini is the wrong length")

        file_split = split[2].split(' ')
        self.assertTrue(file_split[2] == self.basetracini)
        
    def testProjectOneDoesNotHaveWGI(self):
        bin_dir = os.path.join(self.location, 'bin')
        result = os.path.exists(os.path.join(bin_dir, 'project1.wsgi'))
        self.assertFalse(result, "Project 1 has generated a wsgi file")
        
    def testProjectTwoDoesNotHaveWSGI(self):
        bin_dir = os.path.join(self.location, 'bin')
        result = os.path.exists(os.path.join(bin_dir, 'project2.wsgi'))
        self.assertFalse(result, "Project 2 has generated a wsgi file")
        
    def testMetaWSGI(self):
        bin_dir = os.path.join(self.location, 'bin')
        result = os.path.exists(os.path.join(bin_dir, 'meta-trac.wsgi'))
        self.assertTrue(result, "meta-trac has not generated a wsgi file")

