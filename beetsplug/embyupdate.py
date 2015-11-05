"""Updates the Emby Library whenever the beets library is changed.

    emby:
        host: localhost
        port: 8096
        username: user
        password: password
"""
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from beets import config
from beets.plugins import BeetsPlugin
from urllib import urlencode
from urlparse import urljoin, parse_qs, urlsplit, urlunsplit
import hashlib
import requests


def api_url(host, port, endpoint):
    """Returns a joined url.
    """
    joined = urljoin('http://{0}:{1}'.format(host, port), endpoint)
    scheme, netloc, path, query_string, fragment = urlsplit(joined)
    query_params = parse_qs(query_string)

    query_params['format'] = ['json']
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def password_data(username, password):
    """Returns a dict with username and its encoded password.
    """
    return {
        'username': username,
        'password': hashlib.sha1(password).hexdigest(),
        'passwordMd5': hashlib.md5(password).hexdigest()
    }


def create_headers(user_id, token=None):
    """Return header dict that is needed to talk to the Emby API.
    """
    headers = {
        'Authorization': 'MediaBrowser',
        'UserId': user_id,
        'Client': 'other',
        'Device': 'empy',
        'DeviceId': 'beets',
        'Version': '0.0.0'
    }

    if token:
        headers['X-MediaBrowser-Token'] = token

    return headers


def get_token(host, port, headers, auth_data):
    url = api_url(host, port, '/Users/AuthenticateByName')
    r = requests.post(url, headers=headers, data=auth_data)

    return r.json()['AccessToken']


def get_user(host, port, username):
    """Return user dict from server or None if there is no user.
    """
    url = api_url(host, port, '/Users/Public')
    r = requests.get(url)
    user = [i for i in r.json() if i['Name'] == username]

    if user:
        return user[0]
    else:
        raise ValueError('User not found.')


def update_emby(host, port, username, password):
    """Sends request to Emby API to start a library refresh.
    """
    url = api_url(host, port, '/Library/Refresh')
    token = None

    user = get_user(host, port, username)

    auth_data = password_data(username, password)
    headers = create_headers(user['Id'])
    token = get_token(host, port, headers, auth_data)
    headers = create_headers(user['Id'], token=token)

    # Do the update
    r = requests.post(url, headers=headers)
    if r.status_code != 204:
        raise requests.exceptions.RequestException


class EmbyUpdate(BeetsPlugin):
    def __init__(self):
        super(EmbyUpdate, self).__init__()

        # Adding defaults.
        config['emby'].add({
            u'host': u'localhost',
            u'port': 8096
        })

        self.register_listener('database_change', self.listen_for_db_change)

    def listen_for_db_change(self, lib, model):
        """Listens for beets db change and register the update for the end.
        """
        self.register_listener('cli_exit', self.update)

    def update(self, lib):
        """When the client exists try to send refresh request to Emby.
        """
        self._log.info('Updating Emby library...')

        try:
            update_emby(config['emby']['host'].get(),
                        config['emby']['port'].get())
            self._log.info('... started.')

        except requests.exceptions.RequestException:
            self._log.warning('Update failed.')
