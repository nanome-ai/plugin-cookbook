from notebooks.interface import WebsocketPluginInstance
import os
import sys
# Increase the recursion limit in order to properly serialize Complexes
# recursion_limit = 100000
# sys.setrecursionlimit(recursion_limit)

websocket_url = os.environ.get('WEBSOCKET_SERVER')
session_id = os.environ.get('REDIS_CHANNEL')
print(f'session id {session_id}')
plugin_instance = WebsocketPluginInstance(websocket_url, session_id)
plugin_instance.ws_connect()
breakpoint()
complexes = plugin_instance.request_complex_list()
print(complexes)

comp = plugin_instance.request_complexes([complexes[0].index])[0]
print(list(comp.atoms))
breakpoint()
print("Done.")