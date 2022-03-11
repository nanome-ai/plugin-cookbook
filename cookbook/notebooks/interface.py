import json
import redis
import time
import uuid
import base64
import dill
import io
from nanome import PluginInstance
from nanome._internal._network._serialization._serializer import Serializer
from nanome.util import Logs


def pickle_data(data):
    """Return the stringified bytes of pickled data."""
    bytes_output = io.BytesIO()
    dill.dump(data, bytes_output)
    bytes_output_base64 = base64.b64encode(bytes_output.getvalue()).decode()
    bytes_output.close()
    return bytes_output_base64


def unpickle_data(pickled_data):
    """Unpickle data into its original python version."""
    pickle_bytes = io.BytesIO(base64.b64decode(pickled_data))
    unpickled_data = dill.loads(pickle_bytes.read())
    pickle_bytes.close()
    return unpickled_data


class StreamRedisInterface:
    """Gets wrapped around a stream object on creation, and is used to send data to the stream through redis.

    The PluginService has functions set up to handle streams, because streams on the client side aren't networked.
    This should not be called explicitly, but used through the RedisPluginInterface class.
    """

    def __init__(self, stream_data, plugin_interface):
        self.stream_id = stream_data['stream_id']
        self._plugin_interface = plugin_interface


    def update(self, stream_data):
        response = self._plugin_interface._rpc_request(
            'stream_update', args=[self.stream_id, stream_data])
        return response

    def destroy(self):
        response = self._plugin_interface._rpc_request(
            'stream_destroy', args=[self.stream_id])
        return response


class RedisNetwork:
    """"Replacement for _ProcessNetwork class that routes messages through Redis."""

    def __init__(self, redis_host, redis_port, redis_password, redis_channel=None):
        self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
        self.channel = redis_channel
        self.serializer = Serializer()
        if redis_channel:
            print("Getting Plugin data")
            self.plugin_data = self.get_plugin_data()
        self._command_id = 0

    def _send(self, code, arg, expects_response):
        version_table = self.plugin_data['version_table']
        to_send = self.serializer.serialize_message(self._command_id, code, arg, version_table, expects_response)
        self._rpc_request(to_send=to_send)
        self._command_id += 1
    
    def set_channel(self, value):
        self.channel = value

    def serialize_message(self, code, args):
        """Return serialized command messages as expected by NTS."""
        command_id = self._command_id
        version_table = self.plugin_data['version_table']
        expects_response = True
        to_send = self.serializer.serialize_message(command_id, code, args, version_table, expects_response)
        self._command_id += 1
        return to_send

    def get_plugin_data(self):
        """Retrieve data from plugin required for serialization.
        :arg: shape_list: List of shapes to upload.
        :rtype: list. List of shape IDs.
        """
        function_name = 'get_plugin_data'
        response = self._rpc_request(function_name)
        return response

    def _rpc_request(self, function_name=None, args=None, kwargs=None, to_send=None):
        """Publish an RPC request to redis, and await response.
        :rtype: data returned by PluginInstance function called by RPC.
        """
        args = args or []
        kwargs = kwargs or {}

        # Set random channel name for response
        response_channel = str(uuid.uuid4())
        payload = {
            'response_channel': response_channel
        }
        if to_send is not None:
            payload.update({
                'to_send': to_send.tobytes().decode('utf-8')
            })
        elif function_name is not None:
            payload.update({
                'function': function_name,
                'args': pickle_data(args),
                'kwargs': pickle_data(kwargs),
            })
        message = json.dumps(payload)
        Logs.message(f"Sending {function_name} Request to Redis Channel {self.channel}")
        # Subscribe to response channel before publishing message
        pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(response_channel)
        self.redis.publish(self.channel, message)

        timeout = time.time() + 60
        for message in pubsub.listen():

            if time.time() > timeout:
                pubsub.unsubscribe()
                raise Exception("Timeout error")

            if message.get('type') == 'message':
                response_channel = next(iter(pubsub.channels.keys())).decode('utf-8')
                Logs.message(f"Response received on channel {response_channel}")
                response_data = self.unpickle_message(message)
                pubsub.unsubscribe()
                return response_data

    @staticmethod
    def unpickle_message(message):
        """Unpickle data from Redis message, and return contents."""
        pickled_data = message['data']
        response_data = unpickle_data(pickled_data)
        return response_data


class RedisPluginInstance(PluginInstance):

    def setup_redis_network(self, redis_host, redis_port, redis_password, redis_channel=None):
        self._network = RedisNetwork(
            redis_host, redis_port, redis_password, redis_channel=redis_channel)

    def upload_shapes(self, shape_list):
        """Upload a list of shapes to the server.
        :arg: shape_list: List of shapes to upload.
        :rtype: list. List of shape IDs.
        """
        function_name = 'upload_shapes'
        args = [shape_list]
        response = self._rpc_request(function_name, args=args)
        return response

    def create_writing_stream(self, atom_indices, stream_type):
        """Return a stream wrapped in the RedisStreamInterface"""
        function_name = 'create_writing_stream'
        args = [atom_indices, stream_type]
        stream, error = self._rpc_request(function_name, args=args)
        if stream:
            stream_interface = StreamRedisInterface(stream, self)
            response = (stream_interface, error)
        return response


class PluginInstanceWebsocketInterface:

    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.websocket = None
        self.websocket_connected = False


class PluginInstanceRedisInterface:
    """Provides interface for publishing PluginInstance RPC requests over Redis.

    The idea is to feel like you're using the standard
    PluginInstance, but all calls are being made through Redis.
    """

    def __init__(self, redis_host, redis_port, redis_password, redis_channel=None):
        """Initialize the Connection to Redis."""
        self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
        self.plugin_class = PluginInstance
        self.channel = redis_channel

    def set_channel(self, value):
        self.channel = value

    def __getattr__(self, name):
        """Override superclass getattr to provide a proxy for the PluginInstance class.

        If a user calls an attribute on the Interface that exists on the PluginInstance,
        return a proxy call to Redis.
        """
        plugin_instance_api = iter(attr for attr in dir(self.plugin_class) if not attr.startswith('_'))
        interface_override = iter(attr for attr in dir(self) if not attr.startswith('_'))
        # Only intercept if the property is a public property of a PluginInstance,
        # and theres no override on this class.
        if name in plugin_instance_api and name not in interface_override:
            def proxy_redis_message(*args, **kwargs):
                response = self._rpc_request(name, args, kwargs)
                return response
            return proxy_redis_message
        return getattr(self, name)

    def create_writing_stream(self, atom_indices, stream_type):
        """Return a stream wrapped in the RedisStreamInterface"""
        function_name = 'create_writing_stream'
        args = [atom_indices, stream_type]
        stream, error = self._rpc_request(function_name, args=args)
        if stream:
            stream_interface = StreamRedisInterface(stream, self)
            response = (stream_interface, error)
        return response

    def create_plugin_message(self, function_name, response_channel, args=None, kwargs=None,):
        args = args or []
        kwargs = kwargs or {}
        # Set random channel name for responsz
        message = json.dumps({
            'function': function_name,
            'args': args,
            'kwargs': kwargs,
            'args': pickle_data(args),
            'kwargs': pickle_data(kwargs),
            'response_channel': response_channel
        })
        return message

    def _rpc_request(self, function_name, args=None, kwargs=None):
        """Publish an RPC request to redis, and await response.

        :rtype: data returned by PluginInstance function called by RPC.
        """
        args = args or []
        kwargs = kwargs or {}
        response_channel = str(uuid.uuid4())
        message = self.create_plugin_message(function_name, response_channel, args, kwargs)
        Logs.message(f"Sending {function_name} Request to Redis Channel {self.channel}")
        # Subscribe to response channel before publishing message
        pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(response_channel)
        self.redis.publish(self.channel, message)

        timeout = time.time() + 60
        for message in pubsub.listen():

            if time.time() > timeout:
                pubsub.unsubscribe()
                raise Exception("Timeout error")

            if message.get('type') == 'message':
                response_channel = next(iter(pubsub.channels.keys())).decode('utf-8')
                Logs.message(f"Response received on channel {response_channel}")
                response_data = self.unpickle_message(message)
                pubsub.unsubscribe()
                return response_data

    @staticmethod
    def unpickle_message(message):
        """Unpickle data from Redis message, and return contents."""
        pickled_data = message['data']
        response_data = unpickle_data(pickled_data)
        return response_data

    def upload_shapes(self, shape_list):
        """Upload a list of shapes to the server.

        :arg: shape_list: List of shapes to upload.
        :rtype: list. List of shape IDs.
        """
        function_name = 'upload_shapes'
        args = [shape_list]
        response = self._rpc_request(function_name, args=args)
        return response

    def get_plugin_data(self):
        """Upload a list of shapes to the server.

        :arg: shape_list: List of shapes to upload.
        :rtype: list. List of shape IDs.
        """
        function_name = 'get_plugin_data'
        response = self._rpc_request(function_name)
        return response
