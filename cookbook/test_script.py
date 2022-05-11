import os
import sys

from schemas import AtomSchema
from interface import PluginInstanceRedisInterface


# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''

# When your PluginService is running, you can get your channel value from the Logs, or from the query parameter in your open browser.
# Update this value to match that, so that your commands will run against your live workspace.
redis_channel = os.environ.get("REDIS_CHANNEL")


plugin_instance = PluginInstanceRedisInterface(redis_host, redis_port, redis_password, redis_channel)

comp_list = plugin_instance.request_complex_list()

comp = comp_list[0]

comp.boxed = not comp.boxed
output = plugin_instance.update_structures_shallow([comp])
print(output)
