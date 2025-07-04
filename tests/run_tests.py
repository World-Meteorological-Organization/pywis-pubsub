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
import os
import unittest
from unittest.mock import patch

from requests import Session
from pywis_pubsub.errors import TestSuiteError
from pywis_pubsub.ets import WNMTestSuite
from pywis_pubsub.kpi import calculate_grade, WNMKeyPerformanceIndicators
from pywis_pubsub.verification import verify_data

TESTDATA_DIR = os.path.dirname(os.path.realpath(__file__))


def get_abspath(filepath):
    """helper function to facilitate absolute test file access"""

    return os.path.join(TESTDATA_DIR, filepath)


def msg(test_id, test_description):
    """convenience function to print out test id and desc"""
    return f'{test_id}: {test_description}'


class PyWISPubSubTest(unittest.TestCase):
    """Test suite for package pywis_pubsub"""
    def setUp(self):
        """setup test fixtures, etc."""
        print(msg(self.id(), self.shortDescription()))

    def tearDown(self):
        """return to pristine state"""
        pass

    @patch.object(Session, 'get')
    def test_verification(self, mock_get):
        """Test verification"""

        data_filename = 'A_SZIO01AMMC110648_C_EDZW_20230811064904_50549867'

        with open(get_abspath(data_filename), 'rb') as fh:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = fh.read()

        with open(get_abspath('test_valid_checksum.json')) as fh:
            data = json.load(fh)
            is_valid = verify_data(data, True)
            self.assertTrue(is_valid)


class WNMETSTest(unittest.TestCase):
    """WNM tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_pass(self):
        """Simple tests for a passing record"""
        with open(get_abspath('test_valid.json')) as fh:
            ts = WNMTestSuite(json.load(fh))
            results = ts.run_tests()

            codes = [r['code'] for r in results['ets-report']['tests']]

            self.assertEqual(codes.count('FAILED'), 0)
            self.assertEqual(codes.count('PASSED'), 7)
            self.assertEqual(codes.count('SKIPPED'), 0)

    def test_fail(self):
        """Simple tests for a failing record"""
        with open(get_abspath('test_invalid_datetime.json')) as fh:
            record = json.load(fh)
            ts = WNMTestSuite(record)
            results = ts.run_tests()

            codes = [r['code'] for r in results['ets-report']['tests']]

            self.assertEqual(codes.count('FAILED'), 1)
            self.assertEqual(codes.count('PASSED'), 6)
            self.assertEqual(codes.count('SKIPPED'), 0)

            with self.assertRaises(ValueError):
                ts.run_tests(fail_on_schema_validation=True)

        with self.assertRaises(ValueError):
            with open(get_abspath('test_invalid.json')) as fh:
                record = json.load(fh)
                ts = WNMTestSuite(record)
                results = ts.run_tests(fail_on_schema_validation=True)

                codes = [r['code'] for r in results['ets-report']['tests']]

                self.assertEqual(codes.count('FAILED'), 1)
                self.assertEqual(codes.count('PASSED'), 6)
                self.assertEqual(codes.count('SKIPPED'), 0)

        with self.assertRaises(json.decoder.JSONDecodeError):
            with open(get_abspath('test_malformed.json')) as fh:
                record = json.load(fh)
                ts = WNMTestSuite(record)
                results = ts.run_tests()

    def test_raise_for_status(self):
        """Simple test for raise_for_status"""

        with open(get_abspath('test_valid.json')) as fh:
            ts = WNMTestSuite(json.load(fh))
            _ = ts.run_tests(fail_on_schema_validation=True)

            assert ts.raise_for_status() is None

        with open(get_abspath('test_invalid_uuid.json')) as fh:
            ts = WNMTestSuite(json.load(fh))
            _ = ts.run_tests(fail_on_schema_validation=True)

            with self.assertRaises(TestSuiteError):
                ts.raise_for_status()


class WNMKPITest(unittest.TestCase):
    """WNM KPI tests of tests"""

    def setUp(self):
        """setup test fixtures, etc."""
        pass

    def tearDown(self):
        """return to pristine state"""
        pass

    def test_kpi_evaluate(self):
        file_ = 'test_valid.json'
        with open(get_abspath(file_)) as fh:
            data = json.load(fh)

        kpis = WNMKeyPerformanceIndicators(data)

        results = kpis.evaluate()

        self.assertEqual(results['summary']['total'], 2)
        self.assertEqual(results['summary']['score'], 0)
        self.assertEqual(results['summary']['percentage'], 0)
        self.assertEqual(results['summary']['grade'], 0)

    def test_calculate_grade(self):
        self.assertEqual(calculate_grade(98), 'A')
        self.assertEqual(calculate_grade(77), 'B')
        self.assertEqual(calculate_grade(66), 'B')
        self.assertEqual(calculate_grade(52), 'C')
        self.assertEqual(calculate_grade(41), 'D')
        self.assertEqual(calculate_grade(33), 'E')
        self.assertIsNone(calculate_grade(None))

        with self.assertRaises(ValueError):
            calculate_grade(101)


if __name__ == '__main__':
    unittest.main()
