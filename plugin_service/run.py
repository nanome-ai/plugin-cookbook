import nanome
from nanome.service import PluginService


def main():
    name = '[wip] Browser Plugin.'
    description = 'Test deploying a Flask application with your plugin.'
    tags = ['UI']
    advanced_options = False
    plugin = nanome.Plugin(name, description, tags, advanced_options)
    plugin.set_plugin_class(PluginService)
    plugin.run()


if __name__ == '__main__':
    main()
