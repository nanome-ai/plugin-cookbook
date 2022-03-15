import asyncio
import base64
import dill
import io
import json
import os
import struct
import websockets
import enum

import nanome
from nanome.util import async_callback, Logs
from nanome.util.enums import NotificationTypes
from nanome._internal._util._serializers import _TypeSerializer
from nanome._internal._network import _Packet

BASE_PATH = os.path.dirname(f'{os.path.realpath(__file__)}')
MENU_PATH = os.path.join(BASE_PATH, 'default_menu.json')

WEBSOCKET_SERVER = os.environ.get('WEBSOCKET_SERVER')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')


class MESSAGE_TYPES:
    """Enum for message types that can be handled by plugin."""
    JOIN = 'join'
    CLOSE = 'close'
    FN_CALL = 'fn_call'
    SERIALIZED_MESSAGE = 'serialized_message'


class WebsocketPlugin(nanome.AsyncPluginInstance):

    @async_callback
    async def start(self):
        self.websocket_url =  WEBSOCKET_SERVER
        self.session_id = os.environ.get("REDIS_CHANNEL")  # TODO: rename
        Logs.message(f"Using Session ID {self.session_id}")
        await self.ws_connect()
        self.on_run()
        self.ws_loop()
    
    @async_callback
    async def on_run(self):
        default_url = os.environ.get('DEFAULT_URL')
        jupyter_token = os.environ.get('JUPYTER_TOKEN')
        url = f'{default_url}?token={jupyter_token}'
        print(f'Opening {url}')
        self.open_url(url)

    async def ws_connect(self):
        Logs.debug(f'connecting to {self.websocket_url}')

        while True:
            try:
                self.ws = await websockets.connect(self.websocket_url)
                break
            except:
                await asyncio.sleep(1)

        Logs.debug(f'connected to {self.websocket_url}')
        await self.ws_send('host', self.session_id)

    async def ws_send(self, type, data):
        msg = json.dumps({'type': type, 'data': data})
        await self.ws.send(msg)

    @async_callback
    async def ws_loop(self):
        while True:
            response = None
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosedError:
                await self.ws_connect()
                continue

            Logs.message("Attempting to load json")
            message = json.loads(message)
            message_type = message.get('type')
            message_data = message.get('data')
            Logs.message(f"received message {message_type}")
            if message_type in [MESSAGE_TYPES.JOIN, MESSAGE_TYPES.CLOSE]:
                # ignore non-data messages
                Logs.message("Ignoring non-data message type")
                continue
            elif message_type == MESSAGE_TYPES.FN_CALL:
                response = await self.handle_fn_call(message_data)
            elif message_type == MESSAGE_TYPES.SERIALIZED_MESSAGE:
                to_send = str.encode(message_data)
                response = self.send_to_nts(to_send)
            error_message = 'JSON Decode Failure'
            self.send_notification(NotificationTypes.error, error_message)

            if response:
                await self.ws_send('function_response', response)
    
    def send_to_nts(self, to_send):
        to_send = to_send
        network = self._network
        command_id = network._command_id
        packet = _Packet()
        packet.set(network._session_id, _Packet.packet_type_message_to_client, network._plugin_id)
        packet.write(to_send)
        # if code != 0: # Messages.connect
        #     packet.compress()
        try:
            network._queue_net_out.put(packet)
            asyncio.wait_for(network._queue_net_out.join(), timeout=1)
        except BrokenPipeError:
            pass  # Ignore, as it will be closed later on, during _receive
        network._command_id = (command_id + 1) % 4294967295  # Cap by uint max
        return command_id

    async def handle_fn_call(self, message_data):
        fn_name = message_data['function']
        args = message_data['args']
        kwargs = message_data['kwargs']
        Logs.message(f"Received Request: {fn_name}")

        function_to_call = getattr(self, fn_name)
        try:
            response = await function_to_call(*args, **kwargs)
        except (TypeError, RuntimeError) as e:
            # TypeError Happens when you await a non-sync function.
            # Because nanome-lib doesn't define functions using `async def`,
            # I can't find a reliable way to determine whether we need to await asyncs.
            # For now, just recall the function without async.
            response = function_to_call(*args, **kwargs)
        except struct.error:
            Logs.error(f"Serialization error on {fn_name} call")
        return response

    @staticmethod
    def pickle_data(data):
        """Return the stringified bytes of pickled data."""
        bytes_output = io.BytesIO()
        dill.dump(data, bytes_output)
        bytes_output_base64 = base64.b64encode(bytes_output.getvalue()).decode()
        bytes_output.close()
        return bytes_output_base64

    @staticmethod
    def unpickle_data(pickled_data):
        """Unpickle data into its original python version."""
        pickle_bytes = io.BytesIO(base64.b64decode(pickled_data))
        unpickled_data = dill.loads(pickle_bytes.read())
        pickle_bytes.close()
        return unpickled_data

    def get_plugin_data(self):
        """Return data required for interface to serialize message requests."""
        plugin_id = self._network._plugin_id
        session_id = self._network._session_id
        version_table = _TypeSerializer.get_version_table()
        data = {
            'plugin_id': plugin_id,
            'session_id': session_id,
            'version_table': version_table
        }
        return data