import os
import unittest

from interface import PluginInstanceRedisInterface
from schemas import api_function_definitions
from nanome.api import structure


# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''
redis_channel = os.environ.get("REDIS_CHANNEL")


class APITests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.plugin_instance = PluginInstanceRedisInterface(
            redis_host, redis_port, redis_password, redis_channel)
        # Clear Workspace, and load test structure
        cls.ws = structure.Workspace()
        # test_file = '1tyl.pdb'
        test_file = '1tyl.pdb'
        comp = structure.Complex.io.from_pdb(path=test_file)
        comp.name = test_file
        cls.ws.add_complex(comp)
        cls.plugin_instance.update_workspace(cls.ws)
        # Get updated index of test_comp
        comp_list = cls.plugin_instance.request_complex_list()
        cls.test_comp = cls.plugin_instance.request_complexes([comp_list[0].index])[0]
        assert cls.test_comp.index != -1

    def test_request_complex_list(self):
        comp_list = self.plugin_instance.request_complex_list()
        self.assertTrue(isinstance(comp_list[0], structure.Complex))

    def test_request_complexes(self):
        indices = [self.test_comp.index]
        comp_list = self.plugin_instance.request_complexes(indices)
        comp = comp_list[0]
        self.assertTrue(next(comp.atoms, None) is not None)
    
    @unittest.skip("Not working yet")
    def test_zoom_on_structure(self):
        # Zoom on complex
        self.plugin_instance.zoom_on_structures(self.test_comp.index)
