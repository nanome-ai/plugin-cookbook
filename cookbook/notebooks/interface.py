import json
from unittest import expectedFailure
import websocket
from nanome import PluginInstance
from nanome._internal._network._serialization._serializer import Serializer
from nanome.util import Logs


class WebsocketNetwork:
    
    def __init__(self, websocket_url, session_id):
        self.websocket_url = websocket_url
        self.websocket = None
        self.websocket_connected = False
        self.session_id = session_id
        self.serializer = Serializer()
        self._command_id = 0

    def ws_send(self, type, data):
        message = json.dumps({'type': type, 'data': data})
        self.ws.send(message)
    
    def _send(self, code, arg, expects_response):
        version_table = self.plugin_data['version_table']
        to_send = self.serializer.serialize_message(self._command_id, code, arg, version_table, expects_response)
        to_send = to_send.tobytes().decode('utf-8')
        self.ws_send('serialized_message', to_send)
        self._command_id += 1
        if expects_response:
            response = self.ws.recv()
            response_data = self.serializer.deserialize_message(response)
            return response_data

    def ws_recv(self):
        response = self.ws.recv()
        return response

    def connect(self):
        Logs.debug(f'connecting to {self.websocket_url}')
        self.ws = websocket.WebSocket()
        self.ws.connect(self.websocket_url)
        Logs.debug(f'connected to {self.websocket_url}')
        self.ws_send('join', self.session_id)
        self.plugin_data = self.get_plugin_data()
    
    def get_plugin_data(self):
        """Retrieve data from plugin required for serialization.
        :arg: shape_list: List of shapes to upload.
        :rtype: list. List of shape IDs.
        """
        function_name = 'get_plugin_data'
        data = {'function': function_name, "args": [], "kwargs": {}}
        self.ws_send("fn_call", data)
        response = self.ws_recv()
        response_data = json.loads(response)['data']
        return response_data



class WebsocketPluginInstance(PluginInstance):

    def __init__(self):
        super().__init__()
    
    def ws_connect(self, websocket_url, session_id):
        self._network = WebsocketNetwork(websocket_url, session_id)
        self._network.connect()
