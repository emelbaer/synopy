# -*- coding: utf-8 -*-
import json
from urlparse import urljoin

import requests

from errors import format_error


WEBAPI_PREFIX = 'webapi'


class Authentication(object):
    def __init__(self, sid, format='cookie'):
        assert format in ('cookie', 'sid'), "invalid sid format"

        self.sid = sid
        self.format = format

    def build_params(self):
        auth = {}
        sid_key = self.format == 'cookie' and 'id' or '_id'
        auth[sid_key] = self.sid
        return auth


class Connection(object):
    def __init__(self, protocol, domain, auth=None, port=80):
        assert protocol in ('http', 'https'), "invalid protocol"
        assert int(port), "port number must be integer"

        self.protocol = protocol
        self.domain = domain
        self.auth = auth
        self.port = str(port)

    def build_url(self, path):
        base_path = u'://'.join([self.protocol, self.domain])
        base_path = u':'.join([base_path, self.port])
        return urljoin(base_path, path)

    def build_request_options(self, http_method, params, use_auth=False):
        opts = {'params' if http_method == 'get' else 'data': params}
        if use_auth:
            if self.auth.format == 'sid':
                # pass the sid along with the get params
                opts['params'].update(self.auth.build_params())
            else:
                # pass it as a cookie
                opts['cookies'] = self.auth.build_params()
        return opts

    def send(self, path, http_method, namespace, params, use_auth=False):
        http_method = http_method.lower()
        assert http_method in ('get', 'post'), "invalid http method"

        url = self.build_url(path)
        opts = self.build_request_options(http_method, params, use_auth=use_auth)
        if http_method == 'get':
            resp = requests.get(url, **opts)
        else:
            resp = requests.post(url, **opts)
        return self.handle_response(resp, namespace)

    def handle_response(self, resp, namespace):
        response = Response(resp)
        if response.status_code == 200:
            if not response.is_success():
                errno = response.error_code
                response.error_message = format_error(errno, namespace)
        return response


class Response(object):
    def __init__(self, resp):
        # the ``requests`` library response object
        self.raw_response = resp
        # the http status code
        self.status_code = resp.status_code
        # the url that initiated this response
        self.url = resp.url
        # the deserialized json data
        self.payload = resp.status_code == 200 and json.loads(resp.content) or {}
        # user friendly message
        self.error_message = None

    def is_success(self):
        return self.payload.get('success') is True

    @property
    def error_code(self):
        return self.payload.get('error') and self.payload['error']['code'] or None


def _send_command(self, api_method, http_method, params, use_auth=False):
    all_params = self.base_params
    all_params['method'] = api_method
    all_params.update(params)
    return self.conn.send(self.path, http_method, self.namespace, all_params,
                          use_auth=use_auth)


class ApiBaseMeta(type):
    def __init__(cls, name, bases, attrs):
        super(ApiBaseMeta, cls).__init__(name, bases, attrs)
        parents = [b for b in bases if isinstance(b, ApiBaseMeta)]
        if not parents:
            return
        api_methods = attrs.pop('methods')

        def wrapped_send(api_method, http_method, use_auth=False):
            def _wrapped(self, **params):
                return _send_command(self, api_method, http_method, params,
                                     use_auth=use_auth)
            return _wrapped

        for api_method, api_values in api_methods.iteritems():
            func_name = api_values.pop('func_name', api_method)
            http_method = api_values.pop('http_method', 'GET')
            use_auth = api_values.pop('use_auth')
            setattr(
                cls,
                func_name,
                wrapped_send(api_method, http_method, use_auth=use_auth)
            )


class ApiBase(object):
    __metaclass__ = ApiBaseMeta
    path = None
    namespace = None
    methods = None

    def __init__(self, connection, version, namespace_prefix=WEBAPI_PREFIX):
        assert int(version), "port number must be integer"

        self.conn = connection
        self.version = str(version)
        self.prefix = namespace_prefix or u''
        self.path = u'/'.join([self.prefix, self.path])

    @property
    def base_params(self):
        return {
            'api': self.namespace,
            'version': self.version
        }