from nanome.api.structure import Complex
from nanome.util import async_callback, Logs

import argparse
import asyncio
import nanome
import base64
import json
import os
import random
import string
import tempfile
import websockets


IS_DOCKER = os.path.exists('/.dockerenv')
class DataTable(nanome.AsyncPluginInstance):
    @async_callback
    async def start(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_sdf = tempfile.NamedTemporaryFile(delete=False, suffix='.sdf', dir=self.temp_dir.name)

        self.url, self.https = self.custom_data
        self.server_url = 'data-table-server' if IS_DOCKER else self.url
        self.session = ''.join(random.choices(string.ascii_lowercase, k=4))

        self.selected_complex = None
        self.selected_frame = None
        self.selected_is_conformer = False
        self.selected_num_frames = 0
        self.ignore_next_update = 0

        await self.ws_connect()
        self.on_run()
        self.ws_loop()

    async def ws_connect(self):
        ws_url = f'ws://{self.server_url}/ws'
        Logs.debug(f'connecting to {ws_url}')

        while True:
            try:
                self.ws = await websockets.connect(ws_url)
                break
            except:
                await asyncio.sleep(1)

        Logs.debug(f'connected to {ws_url}')
        await self.ws_send('host', self.session)

    async def ws_send(self, type, data):
        msg = json.dumps({'type': type, 'data': data})
        await self.ws.send(msg)

    @async_callback
    async def ws_loop(self):
        while True:
            try:
                m = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosedError:
                await self.ws_connect()
                continue

            msg = json.loads(m)
            type = msg.get('type')
            data = msg.get('data')

            Logs.debug('recv', type, data)

            if type == 'join':
                self.update_complexes()
            elif type == 'delete-frames':
                await self.delete_frames(data)
            elif type == 'reorder-frames':
                await self.reorder_frames(data)
            elif type == 'select-complex':
                await self.select_complex(data)
            elif type == 'select-frame':
                await self.select_frame(data)
            elif type == 'split-frames':
                await self.split_frames(data)

            Logs.debug('done', type)

    def on_run(self):
        protocol = 'https' if self.https else 'http'
        self.open_url(f'{protocol}://{self.url}/{self.session}')

    @async_callback
    async def on_stop(self):
        await self.ws.close()

    @async_callback
    async def update_complexes(self):
        complexes = await self.request_complex_list()
        items = [{'name': c.full_name, 'index': c.index} for c in complexes]
        await self.ws_send('complexes', items)

    def on_complex_added(self):
        self.update_complexes()

    def on_complex_removed(self):
        self.update_complexes()

    @async_callback
    async def on_complex_updated(self, complex):
        Logs.debug('complex updated', complex.index)
        if complex.index != self.selected_complex.index:
            return

        self.selected_complex = complex
        if self.ignore_next_update:
            self.ignore_next_update -= 1
            return

        if self.selected_is_conformer:
            num_frames = next(complex.molecules).conformer_count
        else:
            num_frames = len(list(complex.molecules))

        if num_frames != self.selected_num_frames:
            await self.select_complex(complex.index)
        else:
            frame = self.get_selected_frame(complex)
            await self.ws_send('select-frame', frame)

    def get_selected_frame(self, complex):
        if self.selected_is_conformer:
            return next(complex.molecules).current_conformer
        return complex.current_frame

    async def select_complex(self, index):
        complexes = await self.request_complexes([index])
        if not complexes:
            return

        complex = complexes[0]
        self.selected_complex = complex
        self.selected_is_conformer = len(list(complex.molecules)) == 1
        complex.register_complex_updated_callback(self.on_complex_updated)

        await self.update_table()

    async def select_frame(self, index):
        if self.selected_is_conformer:
            next(self.selected_complex.molecules).set_current_conformer(index)
        else:
            self.selected_complex.set_current_frame(index)

        await self.update_complex()

    async def delete_frames(self, indices):
        indices = sorted(indices, reverse=True)
        if self.selected_is_conformer:
            molecule = next(self.selected_complex.molecules)
            for index in indices:
                molecule.delete_conformer(index)
        else:
            for index in indices:
                del self.selected_complex._molecules[index]

        await self.update_complex()
        await self.update_table()

    async def reorder_frames(self, indices):
        if self.selected_is_conformer:
            molecule = next(self.selected_complex.molecules)
            num_frames = molecule.conformer_count
            for i, index in enumerate(indices):
                molecule.copy_conformer(index, num_frames + i)
            for _ in range(num_frames):
                molecule.delete_conformer(0)
        else:
            molecules = list(self.selected_complex.molecules)
            self.selected_complex._molecules = [molecules[i] for i in indices]
            for molecule in self.selected_complex.molecules:
                molecule.index = -1

        await self.update_complex()
        await self.update_table()

    async def split_frames(self, data):
        indices = data['indices']
        single = data['single']
        name_column = data['name_column']
        source = self.selected_complex.convert_to_frames()
        complexes = []

        if single:
            complex = Complex()
            complex.name = source.name
            for index in indices:
                complex.add_molecule(source._molecules[index])
            complexes.append(complex)
        else:
            for index in indices:
                complex = Complex()
                molecule = source._molecules[index]
                complex.name = molecule.associated[name_column]
                complex.add_molecule(molecule)
                complexes.append(complex)

        Complex.align_origins(source, *complexes)
        await self.update_structures_deep(complexes)
        await self.delete_frames(indices)

    async def update_complex(self):
        self.ignore_next_update += 1
        await self.update_structures_deep([self.selected_complex])

    async def update_table(self):
        frame = self.get_selected_frame(self.selected_complex)

        complex = self.selected_complex.convert_to_frames()
        complex.index = self.selected_complex.index
        self.selected_num_frames = len(list(complex.molecules))
        data = []

        for i, mol in enumerate(complex.molecules):
            data.append({'index': i, **mol.associated})

        await self.ws_send('data', data)
        await self.ws_send('select-frame', frame)
        await self.generate_images(complex)

    async def send_image(self, id):
        path = os.path.join(self.temp_dir.name, f'{id}.png')
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
            await self.ws_send('image', {'id': id, 'data': data})


def main():
    parser = argparse.ArgumentParser(description='Parse arguments for Data Table plugin')
    parser.add_argument('--https', dest='https', action='store_true', help='Enable HTTPS on the Data Table Web UI')
    parser.add_argument('-u', '--url', dest='url', type=str, help='URL of the web server', required=True)
    parser.add_argument('-w', '--web-port', dest='web_port', type=int, help='Custom port for connecting to Data Table Web UI.')
    args, _ = parser.parse_known_args()

    https = args.https
    port = args.web_port
    url = args.url

    if port:
        url = f'{url}:{port}'

    plugin = nanome.Plugin('Data Table', 'A Nanome plugin to view multi-frame structure metadata in a table', 'Analysis', False)
    plugin.set_plugin_class(DataTable)
    plugin.set_custom_data(url, https)
    plugin.run()


if __name__ == '__main__':
    main()