# Nanome Plugin Cookbook

Nanome is an immersive platform for collaborative computationally-driven molecular design. Learn more about Nanome at https://nanome.ai. 


### Hello! Welcome to the Plugin Chef Cookbook. Here you can find all of the basic miniture code snippets to best cook up a Nanome plugin. 
As part of the delicious receipes and how-tos for building plugins, here you will find topics ranging from 'How to import structures' to 'How to change representations".

These how-tos are a supplement to the API documentation (https://nanome.readthedocs.io)


View the Cookbook Jupyter/IPython Notebook directly at https://github.com/nanome-ai/plugin-cookbook/blob/main/notebooks/Cookbook.ipynb


Follow the instructions below so you can spin up the Cookbook and run block by block to better understand how to work with Nanome's Python API. 

## Installation

Use Git to clone this repository to your computer.

### Using Docker

Requires Docker Installed (https://www.docker.com/)

```bash
docker build . -t cookbook
docker run -it  -p 8888:8888 nanome-cookbook
```

### Using local python


```bash
pip install -r requirements.txt
npm install
jupyter-lab
```

# Get Started
## Table of Contents:
<ol>
	<li>Building your first Plugin. <code>notebooks/Plugins.ipynb</code></li>
    <li>Utilizing nanome-lib features. <code>notebooks/Cookbook.ipynb</code></li>
</ol>

## Contributors
@mjrosengrant
@ajm13
