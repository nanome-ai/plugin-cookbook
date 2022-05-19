import os
import unittest
import time
from interface import PluginInstanceRedisInterface
from nanome.api import structure
from nanome.util import enums
from nanome.api.user import PresenterInfo
import logging


# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''
redis_channel = os.environ.get("REDIS_CHANNEL")

logging.basicConfig(level=logging.INFO, format='%(message)s')


class APITestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plugin_instance = PluginInstanceRedisInterface(
            redis_host, redis_port, redis_password, redis_channel)
        # Save current workspace, to reload after tests
        logging.info("Saving current workspace")
        cls.previous_workspace = cls.plugin_instance.request_workspace()
        # Update workspace Workspace, and load test structure
        ws = structure.Workspace()
        test_file = 'test_data/1tyl.pdb'
        comp = structure.Complex.io.from_pdb(path=test_file)
        comp.name = test_file
        ws.add_complex(comp)
        cls.plugin_instance.update_workspace(ws)
        # Get updated index of test_comp
        comp_list = cls.plugin_instance.request_complex_list()
        comp_index = comp_list[0].index
        comp_results = cls.plugin_instance.request_complexes([comp_index])
        cls.test_comp = comp_results[0]
        assert cls.test_comp.index != -1
    
    @classmethod
    def tearDownClass(cls):
        cls.plugin_instance.update_workspace(cls.previous_workspace)
        super().tearDownClass()
    
    def test_request_complex_list(self):
        comp_list = self.plugin_instance.request_complex_list()
        self.assertTrue(isinstance(comp_list[0], structure.Complex))

    def test_request_complexes(self):
        indices = [self.test_comp.index]
        comp_list = self.plugin_instance.request_complexes(indices)
        comp = comp_list[0]
        self.assertTrue(next(comp.atoms, None) is not None)
    
    def test_update_structures_shallow(self):
        self.test_comp.boxed = True
        self.plugin_instance.update_structures_shallow([self.test_comp])
        self.test_comp.boxed = False
        self.plugin_instance.update_structures_shallow([self.test_comp])

    def test_update_structures_deep(self):
        for atom in self.test_comp.atoms:
            atom.set_visible(False)
        self.plugin_instance.update_structures_deep([self.test_comp])
        time.sleep(1)
        for atom in self.test_comp.atoms:
            atom.set_visible(True)
        self.plugin_instance.update_structures_deep([self.test_comp])

    @unittest.skip("Not working yet.")
    def test_zoom_on_structures(self):
        # Zoom on complex
        atom = next(self.test_comp.atoms)
        self.plugin_instance.zoom_on_structures([atom])
    
    @unittest.skip("Not working yet.")
    def test_center_on_structures(self):
        # Center on complex
        self.plugin_instance.center_on_structures([self.test_comp])

    def test_send_notification(self):
        notification_type = enums.NotificationTypes.success
        self.plugin_instance.send_notification(
            notification_type, "Test notification Successful")
    
    def test_open_url(self):
        url = 'https://nanome.ai'
        self.plugin_instance.open_url(url)
    
    def test_request_presenter_info(self):
        presenter_info = self.plugin_instance.request_presenter_info()
        self.assertTrue(isinstance(presenter_info, PresenterInfo))
