"""
Inspired by this blog

https://iwatobipen.wordpress.com/2018/11/27/visualize-pharmacophore-in-rdkit-rdkit/
"""

from nanome.service import PluginService
from nanome.interface import PluginInstanceRedisInterface

# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''

# When your PluginService is running, you can get your channel value from the Logs, or from the query parameter in your open browser.
# Update this value to match that, so that your commands will run against your live workspace.
redis_channel = 'a5e55f3f-7e52-4018-8097-b6be6470e638'
plugin_instance = PluginInstanceRedisInterface()
plugin_instance.configure_redis(redis_host, redis_port, redis_password, redis_channel)
breakpoint()
plugin_instance.request_complex_list()
print('Hello')