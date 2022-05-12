import os

from interface import PluginInstanceRedisInterface

# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''

# When your PluginService is running, you can get your channel value from the Logs, or from the query parameter in your open browser.
# Update this value to match that, so that your commands will run against your live workspace.
redis_channel = os.environ.get("REDIS_CHANNEL")

plugin_instance = PluginInstanceRedisInterface(redis_host, redis_port, redis_password, redis_channel)

print('getting comp list')
comp_list = plugin_instance.request_complex_list()
comp_indices = [cmp.index for cmp in comp_list]
print("getting comp details")
comps = plugin_instance.request_complexes(comp_indices)

comp = comps[0]
print(f'{sum(1 for _ in comp.atoms)} atoms in complex')
comp.boxed = not comp.boxed
print(f"{'Adding' if comp.boxed else 'Removing'} box")
output = plugin_instance.update_structures_shallow([comp])
# print(output)
