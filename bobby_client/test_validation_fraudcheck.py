"""Test BoB Validation API"""

import logging
import os
import unittest

from bobby_client.env import TestEnvironment
from bobby_client.utils import b64e

ISSUER_SIGNATURE_FAST = b64e(os.urandom(32)).decode()
ISSUER_SIGNATURE_SLOW = b64e(os.urandom(32)).decode()

# Lillies väg 2, Lerum
EVENT_START_FAST  = {
    "eventType": "validation",
    "ticketId": "TICKET_ID",
    "mtbReference": {
        "pid": 1,
        "issuerSignature": ISSUER_SIGNATURE_FAST
    },
    'time': '20170521T200000Z',
    'modeOfTransport': 'bus',
    'geo': {
        'lat': 57.770351,
        'long': 12.255959
    }
}

# Lillies väg 2, Lerum
EVENT_START_SLOW = {
    "eventType": "validation",
    "ticketId": "TICKET_ID",
    "mtbReference": {
        "pid": 1,
        "issuerSignature": ISSUER_SIGNATURE_SLOW
    },
    'time': '20170521T200000Z',
    'modeOfTransport': 'bus',
    'geo': {
        'lat': 57.770351,
        'long': 12.255959
    }
}

# Drottningtorget, Göteborg
EVENT_FAST = {
    "eventType": "validation",
    "ticketId": "TICKET_ID",
    "mtbReference": {
        "pid": 1,
        "issuerSignature": ISSUER_SIGNATURE_FAST
    },
    'time': '20170521T201000Z',
    'modeOfTransport': 'bus',
    'geo': {
        'lat': 57.708074,
        'long': 11.973297
    }
}

# Tingshuset, Lerum
EVENT_SLOW = {
    "eventType": "validation",
    "ticketId": "TICKET_ID",
    "mtbReference": {
        "pid": 1,
        "issuerSignature": ISSUER_SIGNATURE_SLOW
    },
    'time': '20170521T200500Z',
    'modeOfTransport': 'bus',
    'geo': {
        'lat': 57.7701897,
        'long': 12.2677485
    }
}


class TestValidationFraudcheckAPI(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.env = TestEnvironment.create_from_config_file(api='validation')
        self.session = self.env.get_session()
        self.env.authenticate(self.session, api='validation')
        raise unittest.SkipTest("No predefined events set")

    def tearDown(self):
        self.session.close()
        self.env.close()

    def test_fraudcheck_fast(self):
        """Test fraudcheck"""

        # create base event
        request_uri = '{}/validation'.format(self.env.endpoint('validation'))
        event = self.env.update_dict_macros(EVENT_START_FAST)
        response = self.session.post("{}/{}".format(request_uri, event['ticketId']), json=event)
        self.assertEqual(response.status_code, 201)

        # submit fraudcheck query
        params = {
            'time': EVENT_FAST['time'],
            'geo': EVENT_FAST['geo'],
            'mtbReference': EVENT_FAST['mtbReference']
        }
        request_uri = '{}/fraudcheck'.format(self.env.endpoint('validation'))
        response = self.session.get(request_uri, json=params)
        self.assertEqual(response.status_code, 200)
        velocity = response.json().get('velocity')
        logging.debug("Got velocity %d km/h", velocity)
        self.assertGreater(velocity, 100)

    def test_fraudcheck_slow(self):
        """Test fraudcheck"""

        # create base event
        request_uri = '{}/validation'.format(self.env.endpoint('validation'))
        event = self.env.update_dict_macros(EVENT_START_SLOW)
        response = self.session.post("{}/{}".format(request_uri, event['ticketId']), json=event)
        self.assertEqual(response.status_code, 201)

        # submit fraudcheck query
        params = {
            'time': EVENT_SLOW['time'],
            'geo': EVENT_SLOW['geo'],
            'mtbReference': EVENT_SLOW['mtbReference']
        }
        request_uri = '{}/fraudcheck'.format(self.env.endpoint('validation'))
        response = self.session.get(request_uri, json=params)
        self.assertEqual(response.status_code, 200)
        velocity = response.json().get('velocity')
        logging.debug("Got velocity %d km/h", velocity)
        self.assertEqual(velocity, 0)


if __name__ == '__main__':
    unittest.main()
