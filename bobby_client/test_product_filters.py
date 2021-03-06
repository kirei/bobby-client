"""Test BoB Product API: Filters"""

import json
import logging
import unittest

from bobby_client.env import TestEnvironment


class TestProductAPIwithFilters(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.env = TestEnvironment.create_from_config_file(api='product')
        self.session = self.env.get_session()
        filename = self.env.config['test']['product'].get('filters')
        if filename is not None:
            with open(filename) as filters_file:
                self.filters = json.load(filters_file)
        else:
            self.filters = {}
        self.env.authenticate(self.session, api='product')
        self.save_results = self.env.config['global'].get('save_results', False)

    def tearDown(self):
        self.session.close()
        self.env.close()

    def _base_test_product(self, filter_type: str):
        """Test product filter using payload or query parameters"""

        test_cases = self.filters.get(filter_type, [])

        if len(test_cases) == 0:
            self.skipTest(f"No filters defined for filter type {filter_type}")

        for test_case in test_cases:

            test_id = test_case.get('id')

            logging.info("Running test %s", test_id)

            request_uri = '{}/product'.format(self.env.endpoint('product'))

            if test_case['operation'] == 'get':
                logging.info("GET: %s", request_uri)
                response = self.session.get(request_uri,
                                            params=test_case.get('query'))
            elif test_case['operation'] == 'post':
                logging.info("POST: %s", request_uri)
                response = self.session.post(request_uri,
                                             params=test_case.get('query'),
                                             json=test_case.get('payload'))
            else:
                raise RuntimeError('Unknown operation: ' + test_case['operation'])

            self.assertEqual(response.status_code, test_case['code'])

            if response.status_code == 200:
                result = response.json()

                if self.save_results:
                    payload_filename = f"{test_id}.json"
                    logging.info("Saving output to %s", payload_filename)
                    with open(payload_filename, 'wt') as output_file:
                        json.dump(result, output_file, indent=4)

                if 'amount' in test_case:
                    unexpected = []
                    for prodset in result:
                        for prod in prodset:
                            prod_amount = prod['fares'][0]['amount']
                            found = None
                            for expect_amount in test_case['amount']:
                                if expect_amount - 0.01 < prod_amount < expect_amount + 0.01:
                                    found = expect_amount
                            if found:
                                test_case['amount'].remove(found)
                            else:
                                unexpected.append(prod_amount)
                    self.assertEqual(unexpected, test_case['amount'])

    def test_product_group_filters(self):
        """Test product group filters"""
        self._base_test_product("group")

    def test_product_query_filters(self):
        """Test product query filters"""
        self._base_test_product("query")

    def test_product_route_filters(self):
        """Test product route filters"""
        self._base_test_product("route")


if __name__ == '__main__':
    unittest.main()
