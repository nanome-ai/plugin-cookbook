# Nanome Plugin Cookbook

Nanome is an immersive VR platform for collaborative computationally-driven molecular design. Learn more about Nanome at https://nanome.ai. 

### Hello! Welcome to the Plugin Chef Cookbook. Here you can find all of the basic miniture code snippets to best cook up a Nanome plugin. 

These how-tos are a supplement to the API documentation (https://nanome.readthedocs.io)

This cookbook uses an experimental process for communicating with a Nanome session from the web browser.
If you run into problems, we encourage you to open a Github issue, or contact the maintainer directly at mike.rosengrant@nanome.ai


## Installation
Requires Docker and Docker Compose
Docker (https://docs.docker.com/get-docker/)
Docker compose (https://docs.docker.com/compose/install/)

1) build and deploy the application. You will need to be able to access the logs.
For arg options, please see https://nanome.readthedocs.io/en/latest/plugins.html#arguments
```bash
./docker/build.sh
./docker/deploy.sh <plugin_args>
docker-compose logs -f
```

2) After the cookbook is started, the logs should print a url which includes an access token. You are going to want to copy this url
```
cookbook_1  Jupyter Server 1.13.1 is running at:
cookbook_1 or http://127.0.0.1:8888/lab?token=590c004ae394b198157e8c1e942bdb7128f4e5325390ff0b
```

3) In Nanome, open your Stacks menu, select the "Cookbook" plugin, and press "Activate" and "Run". This should open your VR Web Browser. It will also print a message to your logs, which contains a channel name for communicating with Redis.


## Overview
- The plugin cookbook is comprised of 2 docker containers deployed using docker-compose, `cookbook`, and `plugin_service`, which communicate via Redis Publish/Subscribe pattern.
- `plugin_service` container runs your standard plugin instance. When activated in Nanome, the plugin sets a Redis channel name, opens your web browser, and passes the channel name as a GET param. When the plugin is run, it subscribes to the Redis channel, and starts polling, waiting to receive messages.
- The `cookbook` container receives the channel name, and publishes messages to that channel that describe what function it wants the plugin instance to run. They message payload is a stringified json blob that looks like,

```
{
  "function": <function_name>
  "args": [...],
  "kwargs": {...},
  "response_channel": "uuid4()"
}
```
the response channel is subscribed to by `cookbook`, and it awaits the response data.
- When the message is received by `plugin_service`, it parses it and executes the provided function with args and kwargs. It then sends the data from the results back the `cookbook`, via the response channel.


# Get Started
## Table of Contents:
<ol>
	<li>Building your first Plugin. <code>notebooks/Plugins.ipynb</code></li>
    <li>Utilizing nanome-lib features. <code>notebooks/Cookbook.ipynb</code></li>
</ol>

## Contributors
@mjrosengrant
@ajm13
