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
# atom_data = {'vdw_radius': 1.55, 'atom_mode': 0, 'atom_color': '<nanome.util.color.Color object at 0x7ff21157b150>', 'symbol': 'N', 'position': [14.885000228881836, 0.5770000219345093, 52.0], 'index': 190292148255, 'atom_rendering': False, 'acceptor': False, 'surface_color': '<nanome.util.color.Color object at 0x7ff21157b890>', 'bfactor': True, 'positions': [[14.885000228881836, 0.5770000219345093, 52.0]], 'atom_scale': 0.5, 'partial_charge': 0.0, 'occupancy': True, 'in_conformer': True, 'current_conformer': 0, 'conformer_count': 1, 'selected': False, 'formal_charge': 0.0, 'is_het': False, 'labeled': False, 'name': 'N', 'exists': True, 'donor': False, 'surface_rendering': False, 'label_text': '', 'polar_hydrogen': False, 'serial': 1, 'alt_loc': '\x00'}
# import schemas
# atom = schemas.AtomSchema().load(atom_data)
# print(atom)

print('getting comp list')
comp_list = plugin_instance.request_complex_list()
comp_indices = [cmp.index for cmp in comp_list]
comps = plugin_instance.request_complexes(comp_indices)

comp = comps[0]
print(sum(1 for _ in comp.atoms))
comp.boxed = not comp.boxed
output = plugin_instance.update_structures_shallow([comp])
# print(output)
