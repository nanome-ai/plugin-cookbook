import base64
import dill
import io
import json
import os
import redis
import struct
import uuid

import nanome
from nanome.util import async_callback, Logs
from nanome.util.enums import NotificationTypes
from nanome._internal._util._serializers import _TypeSerializer
from marshmallow import Schema, fields

import schemas

BASE_PATH = os.path.dirname(f'{os.path.realpath(__file__)}')
MENU_PATH = os.path.join(BASE_PATH, 'default_menu.json')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')


class PluginService(nanome.AsyncPluginInstance):

    @async_callback
    async def start(self):
        # Create Redis channel name to send to frontend to publish to
        redis_channel = os.environ.get('REDIS_CHANNEL')
        self.redis_channel = redis_channel if redis_channel else str(uuid.uuid4())
        Logs.message(f"Starting {self.__class__.__name__} on Redis Channel {self.redis_channel}")
        self.streams = []
        self.shapes = []

    @async_callback
    async def on_run(self):
        default_url = os.environ.get('DEFAULT_URL')
        jupyter_token = os.environ.get('JUPYTER_TOKEN')
        url = f'{default_url}?token={jupyter_token}'
        Logs.message(f'Opening {url}')
        self.open_url(url)
        await self.poll_redis_for_requests(self.redis_channel)

    def deserialize_arg(self, arg_data):
        """Deserialize arguments recursively."""
        if isinstance(arg_data, list):
            for arg_item in arg_data:
                self.deserialize_arg(arg_item)
        if arg_data.__class__ in schemas.structure_schema_map:
            schema_class = schemas.structure_schema_map[arg_data.__class__]
            schema = schema_class()
            arg = schema.load(arg_data)
        return arg

    @async_callback
    async def poll_redis_for_requests(self, redis_channel):
        """Start a non-halting loop polling for and processing Plugin Requests.

        Subscribe to provided redis channel, and process any requests received.
        """
        rds = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
            decode_responses=True)
        pubsub = rds.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(redis_channel)

        for message in pubsub.listen():
            if message.get('type') == 'message':
                try:
                    data = json.loads(message.get('data'))
                except json.JSONDecodeError:
                    error_message = 'JSON Decode Failure'
                    self.send_notification(NotificationTypes.error, error_message)

                Logs.message(f"Received Request: {data.get('function')}")
                fn_name = data['function']
                serialized_args = data['args']
                serialized_kwargs = data['kwargs']
                fn_definition = schemas.api_function_definitions[fn_name]
                fn_args = []
                fn_kwargs = {}
                
                # Deserialize args and kwargs into python classes
                for ser_arg, schema_or_field in zip(serialized_args, fn_definition.params):
                    if isinstance(schema_or_field, Schema):
                        arg = schema_or_field.load(ser_arg)
                    elif isinstance(schema_or_field, fields.Field):
                        # Field that does not need to be deserialized
                        arg = schema_or_field.deserialize(ser_arg)
                    fn_args.append(arg)
                response_channel = data['response_channel']

                function_to_call = getattr(self, fn_name)
                try:
                    response = await function_to_call(*fn_args, **fn_kwargs)
                except (TypeError, RuntimeError) as e:
                    # TypeError Happens when you await a non-sync function.
                    # Because nanome-lib doesn't define functions using `async def`,
                    # I can't find a reliable way to determine whether we need to await asyncs.
                    # For now, just recall the function without async.
                    response = function_to_call(*fn_args, **fn_kwargs)
                except struct.error:
                    Logs.error(f"Serialization error on {fn_name} call")
                Logs.message(response)

                # Serialize response before sending back to client
                output_schema = fn_definition.output
                serialized_response = {}
                if output_schema:
                    if isinstance(output_schema, Schema):
                        serialized_response = output_schema.dump(response)
                    elif isinstance(output_schema, fields.Field):
                        # Field that does not need to be deserialized
                        serialized_response = output_schema.serialize(response)
                json_response = json.dumps(serialized_response)
                response_channel = data['response_channel']
                Logs.message(f'Publishing Response to {response_channel}')
                rds.publish(response_channel, json_response)

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

    async def create_writing_stream(self, indices_list, stream_type, callback=None):
        """After creating stream, save it for future lookups."""
        response = await super().create_writing_stream(indices_list, stream_type, callback=callback)
        stream, error = response
        if stream:
            self.streams.append(stream)

        stream_data = {"stream_id": stream._Stream__id, 'error': error}
        return stream_data

    def stream_update(self, stream_id, stream_data):
        """Function to update stream."""
        stream = next(strm for strm in self.streams if strm._Stream__id == stream_id)
        output = stream.update(stream_data)
        return output

    def stream_destroy(self, stream_id):
        """Function to destroy stream."""
        stream = next(strm for strm in self.streams if strm._Stream__id == stream_id)
        output = stream.destroy()
        return output

    async def upload_shapes(self, shape_list):
        for shape in shape_list:
            Logs.message(shape.index)
        response = await nanome.api.shapes.Shape.upload_multiple(shape_list)
        self.shapes.extend(response)
        for shape in shape_list:
            Logs.message(shape.index)
        return shape_list

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
