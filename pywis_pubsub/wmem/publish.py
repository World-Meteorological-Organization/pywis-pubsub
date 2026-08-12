###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

import json
import logging

import click

from pywis_pubsub import cli_options
from pywis_pubsub import util
from pywis_pubsub.mqtt import MQTTPubSubClient
from pywis_pubsub.wnm.ets import validate


LOGGER = logging.getLogger(__name__)


@click.command()
@click.pass_context
@cli_options.OPTION_CONFIG
@cli_options.OPTION_VERBOSITY
@click.option('--wmem', '-wmem', type=click.File(), help='path to WMEM file')
@click.option('--topic', '-t', help='topic to publish to')
def publish(ctx, wmem, config, topic, verbosity='NOTSET'):
    """Publish a WIS2 Monitoring Event Message"""

    if config is None:
        raise click.ClickException('missing -c/--config')

    if wmem is None:
        raise click.ClickException('missing -wmem/--wmem')

    config = util.yaml_load(config)

    broker = config.get('broker')
    qos = int(config.get('qos', 1))

    options = {
        'verify_certs': config.get('verify_certs', True),
        'certfile': config.get('certfile'),
        'keyfile': config.get('keyfile'),
        'client_id': config.get('client_id')
    }

    if topic is None:
        topic2 = config.get('publish_topic')
    else:
        topic2 = topic

    if config.get('validate_message', False):
        ctx.invoke(validate, message=wmem)
        wmem.seek(0)

    message = json.load(wmem)

    client = MQTTPubSubClient(broker, options)
    click.echo(f'Connected to broker {client.broker_safe_url}')
    click.echo(f'Publishing message to topic={topic2}')
    client.pub(topic2, json.dumps(message, default=util.json_serial), qos)
