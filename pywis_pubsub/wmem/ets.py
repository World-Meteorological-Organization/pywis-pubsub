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

# executable test suite as per WMEM, Annex A

import json
import logging
from uuid import UUID

import click
from jsonschema.validators import Draft202012Validator
import requests

import pywis_pubsub
from pywis_pubsub.errors import TestSuiteError
from pywis_pubsub.bundle import (WMEM_MESSAGE_SCHEMA, WMET_EVENT_TYPE,
                                 WTH_CENTRE_ID)
from pywis_pubsub.util import (get_cli_common_options, get_codelist,
                               get_current_datetime_rfc3339, urlopen_)

LOGGER = logging.getLogger(__name__)


def gen_test_id(test_id: str) -> str:
    """
    Convenience function to print test identifier as URI

    :param test_id: test suite identifier

    :returns: test identifier as URI
    """

    return f'http://wis.wmo.int/spec/wme/1/req/monitoring-event-message-core/{test_id}'  # noqa


class WMEMTestSuite:
    """Test suite for WIS2 Monitoring Event Message"""

    def __init__(self, data: dict):
        """
        initializer

        :param data: dict of WMEM JSON

        :returns: `pywis_pubsub.ets.WMEMTestSuite`
        """

        self.test_id = None
        self.message = data
        self.errors = []
        self.report = []

    def run_tests(self, fail_on_schema_validation=False):
        """Convenience function to run all tests"""

        results = []
        tests = []

        ets_report = {
            'summary': {},
            'generated_by': f'pywis-pubsub {pywis_pubsub.__version__} (https://github.com/World-Meteorological-Organization/pywis-pubsub)'  # noqa
        }

        for f in dir(WMEMTestSuite):
            if all([
                    callable(getattr(WMEMTestSuite, f)),
                    f.startswith('test_requirement'),
                    not f.endswith('validation')]):

                tests.append(f)

        validation_result = self.test_requirement_validation()
        if validation_result['code'] == 'FAILED':
            if fail_on_schema_validation:
                msg = ('Record fails WMEM validation. Stopping ETS ',
                       f"errors: {validation_result['errors']}")
                LOGGER.error(msg)
                raise ValueError(msg)

        for t in tests:
            result = getattr(self, t)()
            results.append(result)
            if result['code'] == 'FAILED':
                self.errors.append(result)

        for code in ['PASSED', 'FAILED', 'SKIPPED']:
            r = len([t for t in results if t['code'] == code])
            ets_report['summary'][code] = r

        ets_report['tests'] = results
        ets_report['datetime'] = get_current_datetime_rfc3339()

        return {
            'ets-report': ets_report
        }

    def raise_for_status(self):
        """
        Raise error if one or more failures were found during validation.

        :returns: `pywcmp.errors.TestSuiteError` or `None`
        """

        if len(self.errors) > 0:
            raise TestSuiteError('Invalid WMEM', self.errors)

    def test_requirement_validation(self):
        """
        Validate that a WMEM is valid to the authoritative WMEM schema.
        """

        validation_errors = []

        status = {
            'id': gen_test_id('validation'),
            'code': 'PASSED'
        }

        if not WMEM_MESSAGE_SCHEMA.exists():
            msg = "WMEM schema missing. Run 'pywis-pubsub bundle sync' to cache"  # noqa
            LOGGER.error(msg)
            raise RuntimeError(msg)

        with WMEM_MESSAGE_SCHEMA.open() as fh:
            LOGGER.debug(f'Validating {self.message} against {WMEM_MESSAGE_SCHEMA}')  # noqa
            validator = Draft202012Validator(json.load(fh))

            for error in validator.iter_errors(self.message):
                LOGGER.debug(f'{error.json_path}: {error.message}')
                validation_errors.append(f'{error.json_path}: {error.message}')

            if validation_errors:
                status['code'] = 'FAILED'
                status['message'] = f'{len(validation_errors)} error(s)'
                status['errors'] = validation_errors

        return status

    def test_requirement_message_size(self):
        """
        Check for the existence of a valid message size.
        """

        status = {
            'id': gen_test_id('message_size'),
            'code': 'PASSED',
        }

        if len(json.dumps(self.message)) > 8192:
            status['code'] = 'FAILED'
            status['message'] = 'Message size exceeds 8192 bytes'

        return status

    def test_requirement_id(self):
        """
        Check for the existence of a valid id property.
        """

        status = {
            'id': gen_test_id('id'),
            'code': 'PASSED',
        }

        try:
            UUID(self.message['id'])
        except ValueError as err:
            status['code'] = 'FAILED'
            status['message'] = f'Invalid UUID: {err}'

        return status

    def test_requirement_version(self):
        """
        Check for the existence of a valid specversion property.
        """

        status = {
            'id': gen_test_id('version'),
            'code': 'PASSED',
        }

        if self.message['specversion'] != '1.0':
            status['code'] = 'FAILED'
            status['message'] = 'Invalid version'

        return status

    def test_requirement_type(self):
        """
        Check for the existence of a valid type.
        """

        status = {
            'id': gen_test_id('type'),
            'code': 'PASSED',
        }

        event_types = get_codelist(WMET_EVENT_TYPE)

        if self.message['type'] not in event_types:
            status['code'] = 'FAILED'
            status['message'] = f"Invalid type: {self.message['type']}"  # noqa

        return status

    def test_requirement_source(self):
        """
        Check for the existence of a valid source property.
        """

        status = {
            'id': gen_test_id('source'),
            'code': 'PASSED'
        }

        centre_ids = get_codelist(WTH_CENTRE_ID)

        if self.message['source'] not in centre_ids:
            status['code'] = 'FAILED'
            status['message'] = f"Invalid centre-id: {self.message['source']}"  # noqa

        return status

    def test_requirement_subject(self):
        """
        Check for the existence of a valid subject property.
        """

        status = {
            'id': gen_test_id('subject'),
            'code': 'PASSED'
        }

        centre_ids = get_codelist(WTH_CENTRE_ID)

        if self.message['subject'] not in centre_ids:
            status['code'] = 'FAILED'
            status['message'] = f"Invalid centre-id: {self.message['subject']}"  # noqa

        return status

    def test_requirement_time(self):
        """
        Check for the existence of a valid time property.
        """

        status = {
            'id': gen_test_id('time'),
            'code': 'PASSED',
            'message': 'Passes given document is compliant/valid'
        }

        return status

    def test_requirement_datacontenttype(self):
        """
        Check for the existence of a valid datacontenttype property.
        """

        status = {
            'id': gen_test_id('datacontenttype'),
            'code': 'PASSED'
        }

        if self.message['datacontenttype'] != 'application/json':
            status['code'] = 'FAILED'
            status['message'] = 'Invalid datacontenttype value'

        return status

    def test_requirement_dataschema(self):
        """
        Check for the existence of a valid dataschema property.
        """

        status = {
            'id': gen_test_id('dataschema'),
            'code': 'PASSED'
        }

        dataschema = self.message['dataschema']

        try:
            schema = requests.get(dataschema).json()
            _ = Draft202012Validator.check_schema(schema)
        except Exception as err:
            status['code'] = 'FAILED'
            status['message'] = f'Invalid JSON Schema: {err}'

        return status

    def test_requirement_data(self):
        """
        Check for the existence of a valid data property.
        """

        status = {
            'id': gen_test_id('data'),
            'code': 'PASSED',
            'message': 'Passes given document is compliant/valid'
        }

        return status

    def test_requirement_data_conformance(self):
        """
        Check for the existence of a valid data conformance property.
        """

        status = {
            'id': gen_test_id('data_conformance'),
            'code': 'PASSED',
            'message': 'Passes given document is compliant/valid'
        }

        return status

    def test_requirement_data_severity(self):
        """
        Check for the existence of a valid data severity property.
        """

        status = {
            'id': gen_test_id('data_severity'),
            'code': 'PASSED',
            'message': 'Passes given document is compliant/valid'
        }

        return status

    def test_requirement_data_content(self):
        """
        Check for the existence of valid data content.
        """

        status = {
            'id': gen_test_id('data_content'),
            'code': 'PASSED'
        }

        if ('links' not in self.message['data'] and
                'content' not in self.message['data']):

            status['code'] = 'FAILED'
            status['message'] = 'Data not found in data.links or data.content'

        return status

    def test_requirement_data_content_title(self):
        """
        Check for the existence of a valid data content title property.
        """

        status = {
            'id': gen_test_id('data_content_title'),
            'code': 'PASSED',
            'message': 'Passes given document is compliant/valid'
        }

        return status

    def test_requirement_data_links(self):
        """
        Check for the existence of valid link objects.
        """

        status = {
            'id': gen_test_id('data_links'),
            'code': 'PASSED'
        }

        if 'content' not in self.message['data']:
            if not self.message['data'].get('links', []):
                status['code'] = 'FAILED'
                status['message'] = 'No valid data found'

            for link in self.message['data']['links']:
                LOGGER.debug('Checking for required protocols')
                if not link['href'].startswith(('http', 'https', 'ftp', 'sftp')):  # noqa
                    status['code'] = 'FAILED'
                    status['message'] = 'Invalid link protocol'

        return status


@click.group()
def ets():
    """executable test suite"""
    pass


@click.command()
@click.pass_context
@get_cli_common_options
@click.argument('file_or_url')
@click.option('--fail-on-schema-validation/--no-fail-on-schema-validation',
              '-f', default=True,
              help='Stop the ETS on failing schema validation')
def validate(ctx, file_or_url, logfile, verbosity,
             fail_on_schema_validation=True):
    """validate against the abstract test suite"""

    click.echo(f'Opening {file_or_url}')

    if file_or_url.startswith('http'):
        content = urlopen_(file_or_url).read()
    else:
        with open(file_or_url) as fh:
            content = fh.read()

    content = json.loads(content.strip())
    click.echo(f'Validating {file_or_url}')

    ts = WMEMTestSuite(content)
    try:
        results = ts.run_tests(fail_on_schema_validation)
    except Exception as err:
        raise click.ClickException(err)

    click.echo(json.dumps(results, indent=4))
    ctx.exit(results['ets-report']['summary']['FAILED'])


ets.add_command(validate)
