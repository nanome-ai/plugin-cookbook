from notebooks.interface import PluginInstanceWebsocketInterface
import os

websocket_url = os.environ.get('WEBSOCKET_SERVER')
plugin_instance = PluginInstanceWebsocketInterface(websocket_url)
plugin_instance.ws_connect()