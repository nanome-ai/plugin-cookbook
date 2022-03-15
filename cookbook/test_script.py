from notebooks.interface import WebsocketPluginInstance
import os

websocket_url = os.environ.get('WEBSOCKET_SERVER')
session_id = os.environ.get('REDIS_CHANNEL')
print(f'session id {session_id}')
plugin_instance = WebsocketPluginInstance()
plugin_instance.ws_connect(websocket_url, session_id)
complexes = plugin_instance.request_complex_list()
print(complexes)

# comp = plugin_instance.request_complexes([complexes[0].index])[0]
# print(list(comp.atoms))
# breakpoint()
# print("Done.")