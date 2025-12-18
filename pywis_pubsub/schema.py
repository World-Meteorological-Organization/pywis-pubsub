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

import click
import logging
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen

from pywis_pubsub import cli_options

LOGGER = logging.getLogger(__name__)

MESSAGE_SCHEMA_URL = 'https://raw.githubusercontent.com/wmo-im/wis2-notification-message/main/schemas/wis2-notification-message-bundled.json'  # noqa
USERDIR = Path.home() / '.pywis-pubsub'

TEMPDIR = tempfile.TemporaryDirectory()
TEMPDIR2 = Path(tempfile.TemporaryDirectory().name)

MESSAGE_SCHEMA = USERDIR / 'wis2-notification-message' / 'wis2-notification-message-bundled.json'  # noqa
MESSAGE_SCHEMA_TEMP = TEMPDIR2 / 'wis2-notification-message' / 'wis2-notification-message-bundled.json'  # noqa


def sync_schema() -> None:
    """
    Sync WIS2 notification schema

    :returns: `None`
    """

    TEMPDIR = tempfile.TemporaryDirectory()
    TEMPDIR2 = Path(tempfile.TemporaryDirectory().name)

    LOGGER.debug('Syncing notification message schema')

    MESSAGE_SCHEMA_TEMP.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.debug('Downloading message schema')
    with MESSAGE_SCHEMA_TEMP.open('wb') as fh:
        fh.write(urlopen(MESSAGE_SCHEMA_URL).read())

    LOGGER.debug(f'Removing {USERDIR}')
    if MESSAGE_SCHEMA.parent.exists():
        shutil.rmtree(USERDIR)

    LOGGER.debug(f'Moving files from {TEMPDIR2} to {USERDIR}')
    MESSAGE_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(MESSAGE_SCHEMA_TEMP, MESSAGE_SCHEMA)

    LOGGER.debug(f'Cleaning up {TEMPDIR}')
    TEMPDIR.cleanup()


@click.group()
def schema():
    """Notification schema management"""
    pass


@click.command()
@click.pass_context
@cli_options.OPTION_VERBOSITY
def sync(ctx, verbosity):
    """Sync WIS2 notification schema"""

    click.echo('Syncing notification message schema')
    sync_schema()


schema.add_command(sync)
