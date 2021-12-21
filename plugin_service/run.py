import os
import nanome

from nanome.service import PluginService
from nanome.api import Plugin
import sys


def main():
    parser = Plugin.create_parser()
    args, _ = parser.parse_known_args()

    default_name = 'Cookbook'
    arg_name = args.name or []
    plugin_name = ' '.join(arg_name) or default_name

    description = 'Interact with your Nanome session via Jupyter Notebook.'
    tags = ['Interactions']

    plugin = nanome.Plugin(plugin_name, description, tags)
    plugin.set_plugin_class(PluginService)

    # CLI Args take priority over environment variables for NTS settnigs
    host = args.host or os.environ.get('NTS_HOST')
    port = args.port or os.environ.get('NTS_PORT') or 0

    configs = {}
    if host:
        configs['host'] = host
    if port:
        configs['port'] = int(port)
    plugin.run(**configs)


if __name__ == '__main__':
    main()
