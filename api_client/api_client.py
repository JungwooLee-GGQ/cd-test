from __future__ import annotations

import logging
import time
from abc import ABC
from typing import Callable

import requests

from app.core.log_config import log_config

log_config()

logger = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class APIClient(ABC):
    RETRIES = 2  # Maximum attempts for API requests when failed
    TIME_TO_WAIT = 3  # Waiting time to resend API request when failed
    PAUSE_WHEN_EXCEEDING_API_LIMIT = 10

    def _http_request(
        self,
        uri: str,
        request: Callable[[str, bool], requests.Response],
        query=None,
        body=None,
        header=None,
    ) -> requests.Response:
        query_params, body_params, headers = self.add_authorization_to_params(
            query, body, header
        )
        for index in range(self.RETRIES):
            try:
                r = request(
                    uri,
                    verify=False,
                    params=query_params,
                    json=body_params,
                    headers=headers,
                )
                r.raise_for_status()
                break
            except requests.HTTPError as e:
                if index == self.RETRIES - 1:
                    break
                code = e.response.status_code
                if code == 404:  # wrong URI. no need to repeat
                    break
                elif code == 429:  # exceeds API limit
                    time.sleep(self.PAUSE_WHEN_EXCEEDING_API_LIMIT)
                else:
                    logger.warning(str(e), exc_info=True)
                    time.sleep(self.TIME_TO_WAIT)
        return r

    def add_authorization_to_params(self, query_params, body_params, headers) -> tuple:
        # Add the authorization to params or headers if API requires it
        return query_params, body_params, headers

    def get_request(self, uri, query=None, body=None, header=None) -> requests.Response:
        return self._http_request(
            uri, requests.get, query=query, body=body, header=header
        )

    def post_request(
        self, uri, query=None, body=None, header=None
    ) -> requests.Response:
        return self._http_request(
            uri, requests.post, query=query, body=body, header=header
        )
