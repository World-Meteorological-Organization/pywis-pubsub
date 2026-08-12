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

WNM_MESSAGE_SCHEMA_URL = 'https://raw.githubusercontent.com/wmo-im/wis2-notification-message/main/schemas/wis2-notification-message-bundled.json'  # noqa
WMEM_MESSAGE_SCHEMA_URL = 'https://raw.githubusercontent.com/wmo-im/wis2-monitoring-events/main/schemas/wis2-event-message-bundled.json'  # noqa
WMET_EVENT_TYPE_URL = 'https://raw.githubusercontent.com/wmo-im/wis2-monitoring-events-codelists/refs/heads/main/codelists/event-type.csv'  # noqa
WTH_CENTRE_ID_URL = 'https://raw.githubusercontent.com/wmo-im/wis2-topic-hierarchy/refs/heads/main/topic-hierarchy/centre-id.csv' # noqa
USERDIR = Path.home() / '.pywis-pubsub'

TEMPDIR = tempfile.TemporaryDirectory()
TEMPDIR_NAME = Path(tempfile.TemporaryDirectory().name)

WNM_MESSAGE_SCHEMA = USERDIR / 'wis2-notification-message' / 'wis2-notification-message-bundled.json'  # noqa
WNM_MESSAGE_SCHEMA_TEMP = TEMPDIR_NAME / 'wis2-notification-message' / 'wis2-notification-message-bundled.json'  # noqa
WMEM_MESSAGE_SCHEMA = USERDIR / 'wis2-monitoring-events' / 'wis2-event-message-bundled.json'  # noqa
WMEM_MESSAGE_SCHEMA_TEMP = TEMPDIR_NAME / 'wis2-monitoring-events' / 'wis2-event-message-bundled.json'  # noqa
WMET_EVENT_TYPE = USERDIR / 'wis2-monitoring-events' / 'event-type.csv'  # noqa
WMET_EVENT_TYPE_TEMP = TEMPDIR_NAME / 'wis2-monitoring-events' / 'event-type.csv'  # noqa
WTH_CENTRE_ID = USERDIR / 'wis2-topic-hierarchy' / 'centre-id.csv'  # noqa
WTH_CENTRE_ID_TEMP = TEMPDIR_NAME / 'wis2-topic-hierarchy' / 'centre-id.csv'  # noqa


def sync_schema() -> None:
    """
    Sync WNM and WMEM schemas

    :returns: `None`
    """

    TEMPDIR = tempfile.TemporaryDirectory()
    TEMPDIR2 = Path(tempfile.TemporaryDirectory().name)

    LOGGER.debug('Syncing WNM schema')

    WNM_MESSAGE_SCHEMA_TEMP.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.debug('Downloading message schema')
    with WNM_MESSAGE_SCHEMA_TEMP.open('wb') as fh:
        fh.write(urlopen(WNM_MESSAGE_SCHEMA_URL).read())

    LOGGER.debug('Syncing WMEM schema')

    WMEM_MESSAGE_SCHEMA_TEMP.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.debug('Downloading message schema')
    with WMEM_MESSAGE_SCHEMA_TEMP.open('wb') as fh:
        fh.write(urlopen(WMEM_MESSAGE_SCHEMA_URL).read())

    LOGGER.debug('Syncing WMET codelists')
    with WMET_EVENT_TYPE_TEMP.open('wb') as fh:
        fh.write(urlopen(WMET_EVENT_TYPE_URL).read())

    WTH_CENTRE_ID_TEMP.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.debug('Syncing WTH codelists')
    with WTH_CENTRE_ID_TEMP.open('wb') as fh:
        fh.write(urlopen(WTH_CENTRE_ID_URL).read())

    LOGGER.debug(f'Removing {USERDIR}')
    if all([WNM_MESSAGE_SCHEMA.parent.exists(),
            WMEM_MESSAGE_SCHEMA.parent.exists(),
            WTH_CENTRE_ID.parent.exists()]):
        shutil.rmtree(USERDIR)

    LOGGER.debug(f'Moving files from {TEMPDIR2} to {USERDIR}')
    WNM_MESSAGE_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    WMEM_MESSAGE_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    WTH_CENTRE_ID.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(WNM_MESSAGE_SCHEMA_TEMP, WNM_MESSAGE_SCHEMA)
    shutil.move(WMEM_MESSAGE_SCHEMA_TEMP, WMEM_MESSAGE_SCHEMA)
    shutil.move(WMET_EVENT_TYPE_TEMP, WMET_EVENT_TYPE)
    shutil.move(WTH_CENTRE_ID_TEMP, WTH_CENTRE_ID)

    LOGGER.debug(f'Cleaning up {TEMPDIR}')
    TEMPDIR.cleanup()


@click.group()
def bundle():
    """Configuration bundle management"""
    pass


@click.command()
@click.pass_context
@cli_options.OPTION_VERBOSITY
def sync(ctx, verbosity):
    """Sync configuration bundle"""

    click.echo('Caching schemas and codelists')
    sync_schema()


bundle.add_command(sync)
