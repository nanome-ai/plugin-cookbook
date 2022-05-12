import os

# Set up redis credentials
redis_host = 'redis'
redis_port = 6379
redis_password = ''

# When your PluginService is running, you can get your channel value from the Logs, or from the query parameter in your open browser.
# Update this value to match that, so that your commands will run against your live workspace.
redis_channel = os.environ.get("REDIS_CHANNEL")

from nanome.util.enums import StreamType
from nanome.interface import PluginInstanceRedisInterface


class ColorStreamPlugin(PluginInstanceRedisInterface):

    def __init__(self, redis_host, redis_port, redis_password, redis_channel=None):
        super().__init__(redis_host, redis_port, redis_password, redis_channel)
        # RGB values of the rainbow
        self.color_index = 0
        self.roygbiv = [
            (255, 0, 0),  # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (75, 0, 130),  # Indigo
            (148, 0, 211),  # Violet
        ]

    def cycle_color(self, comp_indices):
        """For all atom in selected complexes, change their color."""
        comps = self.request_complexes(comp_indices)
        new_color_rgba = self.roygbiv[self.color_index]

        # Create a writing stream to set colors for every atom in the complexes.
        stream_type = StreamType.color
        atom_indices = []
        for comp in comps:
            atom_indices.extend([atom.index for atom in comp.atoms])

        stream = self.create_writing_stream(atom_indices, stream_type)
        if stream.error:
            raise Exception(f"Stream failed to initialize, Please try again. {stream.error}")

        # Set the color for every atom in the stream.
        stream_data = []
        for _ in atom_indices:
            stream_data.extend(new_color_rgba)
        self.color_index = (self.color_index + 1) % len(self.roygbiv)
        stream.update(stream_data)

plugin_instance = ColorStreamPlugin(redis_host, redis_port, redis_password, redis_channel=redis_channel)

comps = plugin_instance.request_complex_list()
comp = comps[0]
print(comp)

# Changing complex color
print("changing comp color")
plugin_instance.cycle_color([comp.index])
plugin_instance.cycle_color([comp.index])
plugin_instance.cycle_color([comp.index])
             