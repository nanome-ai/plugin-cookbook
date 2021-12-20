from interface import PluginInstanceRedisInterface

from nanome.service import PluginService
from nanome.interface import PluginInstanceRedisInterface

# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''

# When your PluginService is running, you can get your channel value from the Logs, or from the query parameter in your open browser.
# Update this value to match that, so that your commands will run against your live workspace.
redis_channel = 'a5100bcd-3b33-48dc-a8b0-67f88182f24e'

plugin_instance = PluginInstanceRedisInterface()
plugin_instance.configure_redis(redis_host, redis_port, redis_password, redis_channel)
print('Hello')