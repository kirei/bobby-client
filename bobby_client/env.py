"""BoB Test Environment"""

import logging
import logging.config
import os
import unittest
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests
from ruamel import yaml

DEFAULT_CONF = "./config.yaml"
DEFAULT_MAX_TTL = 3600
CERT = Tuple[Optional[str], Optional[str]]

class DebugSession(requests.Session):

    def send(self, *args, **kwargs):
        """Send request, log request and response"""

        tag = str(uuid.uuid4())
        request = args[0]
        logging.debug("REQUEST %s METHOD: %s", tag, request.method)
        logging.debug("REQUEST %s URL: %s", tag, request.url)
        logging.debug("REQUEST %s HEADERS: %s", tag, request.headers)
        logging.debug("REQUEST %s CONTENT: %s", tag, request.body)
        logging.debug("REQUEST %s CERT: %s", tag, kwargs.get('cert'))

        proxies = kwargs.get('proxies')
        if proxies is not None:
            logging.debug("REQUEST %s PROXIES: %s", tag, proxies)

        response = super().send(*args, **kwargs)

        logging.debug("RESPONSE %s STATUS: %d", tag, response.status_code)
        logging.debug("RESPONSE %s URL: %s", tag, response.url)
        logging.debug("RESPONSE %s HEADERS: %s", tag, response.headers)
        logging.debug("RESPONSE %s CONTENT: %s", tag, response.text)

        return response


class TestEnvironment(object):
    """BoB Test Environment helper class"""

    def __init__(self, config: Dict, base_dir: str) -> None:
        self.config = config
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)
        self.macros: Dict[str, str] = self.config.get('macros', {})
        self.httpconfig = self.config.get('http')
        self.authconfig: Dict[str, str] = self.config.get('global', {})
        self.entity_id = self.authconfig.get('entity_id')
        self.cert_filename = self.get_filepath(self.authconfig.get('cert'))
        self.key_filename = self.get_filepath(self.authconfig.get('key'))
        config_dict = config.get('logging')
        if config_dict is not None:
            logging.config.dictConfig(config_dict)
        else:
            logging.basicConfig(level=logging.INFO)


    def close(self) -> None:
        """Close test environment"""
        pass

    def endpoint(self, api: str) -> str:
        """Get endpoint by API"""
        return str(self.config['test'][api]['endpoint'])

    def authenticate(self, session: requests.Session, api: Optional[str] = None) -> None:
        """Add BoB authentication to session (use static token if configured)"""
        token = self.authconfig.get('token')
        if token is not None:
            logging.debug("Authentication via static token")
        else:
            logging.debug("Authentication via authentication endpoint")
            token = self.get_auth_jwt_compact(api)
        session.headers["X-BoB-AuthToken"] = token

    def get_session(self) -> requests.Session:
        """Get session with proxies and auth"""
        session = DebugSession()
        session.cert = (self.cert_filename, self.key_filename)
        if self.httpconfig is not None:
            session.verify = self.httpconfig.get('verify', True)
            session.proxies = self.httpconfig.get('proxies')
            session.headers = self.httpconfig.get('headers', {})
        return session

    def get_auth_response(self,
                          api: Optional[str] = None,
                          entity_id: Optional[str] = None,
                          cert: Optional[CERT] = None) -> requests.Response:
        """Get authentication response"""
        if api is not None:
            if 'entity_id' in self.config['test'][api]:
                entity_id = self.config['test'][api]['entity_id']
        if entity_id is None:
            entity_id = self.entity_id
        if cert is None:
            cert = (self.cert_filename, self.key_filename)
        if self.httpconfig is not None:
            verify = self.httpconfig.get('verify', True)
            proxies = self.httpconfig.get('proxies')
        else:
            verify = True
            proxies = None
        endpoint = self.endpoint('authentication')
        request_uri = '{}/auth/{}'.format(endpoint, entity_id)
        with DebugSession() as session:
            response = session.get(url=request_uri, cert=cert, verify=verify, proxies=proxies)
        return response

    def get_auth_jwt_compact(self, api: Optional[str] = None) -> str:
        """Get authentication JWT compact"""
        response = self.get_auth_response(api=api)
        if response.status_code != 200:
            response.raise_for_status()
        data = response.json()
        jwt = data['jwtCompact']
        logging.info("Got BoB authtoken payload: %s", data['payload'])
        logging.debug("Got BoB authtoken JWT: %s", jwt)
        return str(jwt)

    def get_filepath(self, filename: Optional[str] = None) -> Optional[str]:
        """Get absolute file path"""
        if filename is not None:
            return self.base_dir + '/' + filename
        return None

    def update_dict_macros(self, data: dict) -> dict:
        """Update dict values using macros"""
        for key, val in data.items():
            if not isinstance(val, str):
                continue
            if val in self.config['macros']:
                data[key] = self.macros[val]
            elif val == 'UUID':
                data[key] = str(uuid.uuid4())
            elif val == 'TIMESTAMP':
                data[key] = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return data

    @classmethod
    def create_from_config_file(cls, filename: Optional[str] = None, api: List[str] = []) -> object:
        """Load configuration as YAML"""
        filename = filename if filename is not None else os.environ.get('BOBBY_CONFIG')
        filename = filename if filename is not None else DEFAULT_CONF
        logging.debug("Reading configuration from %s", filename)
        with open(filename, "rt") as file:
            config_dict = yaml.load(file, Loader=yaml.Loader)
        base_dir = os.path.dirname(filename)
        if isinstance(api, str):
            api = [api]
        for x in api:
            if x not in config_dict.get('test', {}):
                raise unittest.SkipTest(f"API {api} not configured in {filename}")
        return cls(config_dict, base_dir)
