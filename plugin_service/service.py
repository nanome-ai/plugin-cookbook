import asyncio
import base64
import dill
import io
import json
import os
import random
import redis
import string
import struct
import sys
import uuid
import websockets
import tempfile

import nanome
from nanome.util import async_callback, Logs
from nanome.util.enums import NotificationTypes
from nanome._internal._util._serializers import _TypeSerializer

BASE_PATH = os.path.dirname(f'{os.path.realpath(__file__)}')
MENU_PATH = os.path.join(BASE_PATH, 'default_menu.json')

WEBSOCKET_SERVER = os.environ.get('WEBSOCKET_SERVER')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')


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
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosedError:
                await self.ws_connect()
                continue

            try:
                message = json.loads(message)
                Logs.message(f"got message {message.get('type')}")
                if message.get('type') in ['close', 'join']:
                    # ignore non-data messages
                    continue
                if 'data' in message:
                    data = json.loads(message.get('data'))
                    Logs.debug(data)
                else:
                    continue
            except json.JSONDecodeError:
                error_message = 'JSON Decode Failure'
                self.send_notification(NotificationTypes.error, error_message)

            Logs.message(f"Received Request: {data.get('function')}")
            fn_name = data['function']
            args = self.unpickle_data(data['args'])
            kwargs = self.unpickle_data(data['kwargs'])

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
            Logs.message(response)
            pickled_response = self.pickle_data(response)
            await self.ws_send('function_response', pickled_response)
    
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
