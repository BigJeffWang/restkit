# -*- coding: utf-8 -
#
# Copyright (c) 2008 (c) Benoit Chesneau <benoitc@e-engura.com> 
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

"""
restclient.rest
~~~~~~~~~~~~~~~

This module provide a common interface for all HTTP equest. 

    >>> from restclient import Resource
    >>> res = Resource('http://friendpaste.com')
    >>> res.get('/5rOqE9XTz7lccLgZoQS4IP',headers={'Accept': 'application/json'})
    '{"snippet": "hi!", "title": "", "id": "5rOqE9XTz7lccLgZoQS4IP", "language": "text", "revision": "386233396230"}'
    >>> res.get('/5rOqE9XTz7lccLgZoQS4IP',headers={'Accept': 'application/json'}).http_code
    200
"""
from urllib import quote, urlencode

from restclient.http import getDefaultHTTPClient, HTTPClient 


__all__ = ['Resource', 'RestClient', 'ResourceNotFound', \
        'Unauthorized', 'RequestFailed', 'ResourceError',
        'ResourceResult']
__docformat__ = 'restructuredtext en'


class ResourceError(Exception):
    def __init__(self, message=None, http_code=None, response=None):
        self.message = message
        self.status_code = http_code
        self.response = response

class ResourceNotFound(ResourceError):
    """Exception raised when no resource was found at the given url. 
    """

class Unauthorized(ResourceError):
    """Exception raised when an authorization is required to access to
    the resource specified.
    """

class RequestFailed(ResourceError):
    """Exception raised when an unexpected HTTP error is received in response
    to a request.
    

    The request failed, meaning the remote HTTP server returned a code 
    other than success, unauthorized, or NotFound.

    The exception message attempts to extract the error

    You can get the status code by e.http_code, or see anything about the 
    response via e.response. For example, the entire result body (which is 
    probably an HTML error page) is e.response.body.
    """

class ResourceResult(str):
    """ result returned by `restclient.rest.RestClient`.
    
    you can get result like as string and  status code by result.http_code, 
    or see anything about the response via result.response. For example, the entire 
    result body is result.response.body.

    .. code-block:: python

            from restclient import RestClient
            client = RestClient()
            page = resource.request('GET', 'http://friendpaste.com')
            print page
            print "http code %s" % page.http_code

    """
    def __new__(cls, s, http_code, response):
        self = str.__new__(cls, s)
        self.http_code = http_code
        self.response = response
        return self



class Resource(object):
    """A class that can be instantiated for access to a RESTful resource, 
    including authentication. 

    It can use pycurl, urllib2, httplib2 or any interface over
    `restclient.http.HTTPClient`.

    """
    def __init__(self, uri, httpclient=None):
        """Constructor for a `Resource` object.

        Resource represent an HTTP resource.

        :param uri: str, full uri to the server.
        :param httpclient: any http instance of object based on 
                `restclient.http.HTTPClient`. By default it will use 
                a client based on `pycurl <http://pycurl.sourceforge.net/>`_ if 
                installed or urllib2. You could also use 
                `restclient.http.HTTPLib2HTTPClient`,a client based on 
                `Httplib2 <http://code.google.com/p/httplib2/>`_ or make your
                own depending of the option you need to access to the serve
                (authentification, proxy, ....).
        """

        self.client = RestClient(httpclient)
        self.uri = uri
        self.httpclient = httpclient

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.uri)

    def clone(self):
        """if you want to add a path to resource uri, you can do:

        .. code-block:: python

            resr2 = res.clone()
        
        """
        obj = self.__class__(self.uri, http=self.httpclient)
        return obj
   
    def __call__(self, path):
        """if you want to add a path to resource uri, you can do:
        
        .. code-block:: python

            Resource("/path").get()
        """

        return type(self)(make_uri(self.uri, path), http=self.httpclient)

    
    def get(self, path=None, headers=None, **params):
        """ HTTP GET         
        
        :param path: string  additionnal path to the uri
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request.
        """
        return self.request("GET", path=path, headers=headers, **params)

    def delete(self, path=None, headers=None, **params):
        """ HTTP DELETE

        see GET for params description.
        """
        return self.request("DELETE", path=path, headers=headers, **params)

    def head(self, path=None, headers=None, **params):
        """ HTTP HEAD

        see GET for params description.
        """
        return self.request("HEAD", path=path, headers=headers, **params)

    def post(self, path=None, payload=None, headers=None, **params):
        """ HTTP POST

        :payload: string passed to the body of the request
        :param path: string  additionnal path to the uri
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request
        """

        return self.request("POST", path=path, payload=payload, headers=headers, **params)

    def put(self, path=None, payload=None, headers=None, **params):
        """ HTTP PUT

        see POST for params description.
        """
        return self.request("PUT", path=path, payload=payload, headers=headers, **params)

    def request(self, method, path=None, payload=None, headers=None, **params):
        """ HTTP request

        This method may be the only one you want to override when
        sublclassing `restclient.rest.Resource`.
        
        :payload: string passed to the body of the request
        :param path: string  additionnal path to the uri
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request
        """

        return self.client.make_request(method, self.uri, path=path,
                body=payload, headers=headers, **params)

    def update_uri(self, path):
        """
        to set a new uri absolute path
        """
        self.uri = make_uri(self.uri, path)


class RestClient(object):
    """Basic rest client

        >>> res = RestClient()
        >>> xml = res.get('http://pypaste.com/about')
        >>> json = res.get('http://pypaste.com/3XDqQ8G83LlzVWgCeWdwru', headers={'accept': 'application/json'})
        >>> json
        '{"snippet": "testing API.", "title": "", "id": "3XDqQ8G83LlzVWgCeWdwru", "language": "text", "revision": "363934613139"}'
    """

    def __init__(self, httpclient=None):
        """Constructor for a `RestClient` object.

        RestClient represent an HTTP client.

        :param httpclient: any http instance of object based on 
                `restclient.http.HTTPClient`. By default it will use 
                a client based on `pycurl <http://pycurl.sourceforge.net/>`_ if 
                installed or urllib2. You could also use 
                `restclient.http.HTTPLib2HTTPClient`,a client based on 
                `Httplib2 <http://code.google.com/p/httplib2/>`_ or make your
                own depending of the option you need to access to the serve
                (authentification, proxy, ....).
        """ 

        if httpclient is None:
            httpclient = getDefaultHTTPClient()

        self.httpclient = httpclient

        self.status_code = None
        self.response = None

    def get(self, uri, path=None, headers=None, **params):
        """ HTTP GET         
        
        :param uri: str, uri on which you make the request
        :param path: string  additionnal path to the uri
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request.
        """

        return self.make_request('GET', uri, path=path, headers=headers, **params)

    def head(self, uri, path=None, headers=None, **params):
        """ HTTP HEAD

        see GET for params description.
        """
        return self.make_request("HEAD", uri, path=path, headers=headers, **params)

    def delete(self, uri, path=None, headers=None, **params):
        """ HTTP DELETE

        see GET for params description.
        """
        return self.make_request('DELETE', uri, path=path, headers=headers, **params)

    def post(self, uri, path=None, body=None, headers=None, **params):
        """ HTTP POST

        :param uri: str, uri on which you make the request
        :body: string passed to the body of the request
        :param path: string  additionnal path to the uri
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request
        """
        return self.make_request("POST", uri, path=path, body=body, headers=headers, **params)

    def put(self, uri, path=None, body=None, headers=None, **params):
        """ HTTP PUT

        see POST for params description.
        """

        return self.make_request('PUT', uri, path=path, body=body, headers=headers, **params)

    def make_request(self, method, uri, path=None, body=None, headers=None, **params):
        """ Perform HTTP call support GET, HEAD, POST, PUT and DELETE.
        
        Usage example, get friendpaste page :

        .. code-block:: python

            from restclient import RestClient
            client = RestClient()
            page = resource.request('GET', 'http://friendpaste.com')

        Or get a paste in JSON :

        .. code-block:: python

            from restclient import RestClient
            client = RestClient()
            client.make_request('GET', 'http://friendpaste.com/5rOqE9XTz7lccLgZoQS4IP'),
                headers={'Accept': 'application/json'})

        :param method: str, the HTTP action to be performed: 
            'GET', 'HEAD', 'POST', 'PUT', or 'DELETE'
        :param path: str or list, path to add to the uri
        :param data: str or string or any object that could be
            converted to JSON.
        :param headers: dict, optionnal headers that will
            be added to HTTP request.
        :param params: Optionnal parameterss added to the request.
        
        :return: str.
        """
        
        headers = headers or {}

        resp, data = self.httpclient.request(make_uri(uri, path, **params), method=method,
                body=body, headers=headers)

        status_code = int(resp.status)

        if status_code >= 400:
            if type(data) is dict:
                error = (data.get('error'), data.get('reason'))
            else:
                error = data

            if status_code == 404:
                raise ResourceNotFound(error, http_code=404, response=resp)
            elif status_code == 401 or status_code == 403:
                raise Unauthorized(error, http_code=status_code,
                        response=resp)
            else:
                raise RequestFailed(error, http_code=status_code,
                        response=resp)

        return ResourceResult(data, status_code, resp)


def make_uri(base, *path, **query):
    """Assemble a uri based on a base, any number of path segments, and query
    string parameters.

    >>> make_uri('http://example.org/', '/_all_dbs')
    'http://example.org/_all_dbs'
    """

    if base and base.endswith("/"):
        base = base[:-1]
    retval = [base]

    # build the path
    path = '/'.join([''] +
                    [unicode_quote(s.strip('/')) for s in path
                     if s is not None])
    if path:
        retval.append(path)

    params = []
    for k, v in query.items():
        if type(v) in (list, tuple):
            params.extend([(name, i) for i in v if i is not None])
        elif v is not None:
            params.append((k,v))
    if params:
        retval.extend(['?', unicode_urlencode(params)])
    return ''.join(retval)

def unicode_quote(string, safe=''):
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    return quote(string, safe)

def unicode_urlencode(data):
    if isinstance(data, dict):
        data = data.items()
    params = []
    for name, value in data:
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        params.append((name, value))
    return urlencode(params)

