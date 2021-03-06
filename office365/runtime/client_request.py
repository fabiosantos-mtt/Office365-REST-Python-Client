import requests
from requests import HTTPError
from office365.runtime.client_request_exception import ClientRequestException
from office365.runtime.client_result import ClientResult
from office365.runtime.odata.odata_encoder import ODataEncoder
from office365.runtime.utilities.http_method import HttpMethod
from office365.runtime.utilities.request_options import RequestOptions


class ClientRequest(object):
    """Generic client request for Office365 ODATA/REST service"""

    def __init__(self, context):
        self.context = context
        self.__queries = []
        self.__resultObjects = {}
        self.__events_list = {}

    def clear(self):
        self.__queries = []
        self.__resultObjects = {}
        self.__events_list = {}

    def build_request(self, query):
        request = RequestOptions(query.url)
        # set json format headers
        request.set_headers(self.context.json_format.build_http_headers())
        # set method
        request.method = query.method
        # set request payload
        if query.payload is not None:
            request.data = ODataEncoder(self.context.json_format).default(query.payload)
        return request

    def execute_query(self):
        """Submit pending request to the server"""
        try:
            for query in self.__queries:
                request = self.build_request(query)
                if 'BeforeExecuteQuery' in self.__events_list:
                    self.__events_list['BeforeExecuteQuery'](request, query)
                response = self.execute_request_direct(request)
                result_object = self.__resultObjects.get(query)
                self.process_response(response, result_object)
                if 'AfterExecuteQuery' in self.__events_list:
                    self.__events_list['AfterExecuteQuery'](result_object)
        finally:
            self.clear()

    def process_response(self, response, result_object):
        self.validate_response(response)
        if response.headers.get('Content-Type', '').lower().split(';')[0] != 'application/json':
            if isinstance(result_object, ClientResult):
                result_object.value = response.content
            return

        payload = response.json()
        if payload and result_object is not None:
            json_format = self.context.json_format
            if json_format.security_tag_name:
                payload = payload[json_format.security_tag_name]
            if json_format.collection_tag_name in payload:
                payload = {
                    "collection": payload[json_format.collection_tag_name],
                    "next": payload.get(json_format.collection_next_tag_name, None)
                }
            result_object.map_json(payload)

    def execute_request_direct(self, request_options):
        """Execute client request"""
        self.context.authenticate_request(request_options)
        if request_options.method == HttpMethod.Post:
            if hasattr(request_options.data, 'decode') and callable(request_options.data.decode):
                result = requests.post(url=request_options.url,
                                       headers=request_options.headers,
                                       data=request_options.data,
                                       auth=request_options.auth)
            elif hasattr(request_options.data, 'read') and callable(request_options.data.read):
                result = requests.post(url=request_options.url,
                                       headers=request_options.headers,
                                       data=request_options.data,
                                       auth=request_options.auth)
            else:
                result = requests.post(url=request_options.url,
                                       headers=request_options.headers,
                                       json=request_options.data,
                                       auth=request_options.auth)
        elif request_options.method == HttpMethod.Patch:
            result = requests.patch(url=request_options.url,
                                    headers=request_options.headers,
                                    json=request_options.data,
                                    auth=request_options.auth)
        elif request_options.method == HttpMethod.Delete:
            result = requests.delete(url=request_options.url,
                                     headers=request_options.headers,
                                     auth=request_options.auth)
        elif request_options.method == HttpMethod.Put:
            result = requests.put(url=request_options.url,
                                  data=request_options.data,
                                  headers=request_options.headers,
                                  auth=request_options.auth)
        else:
            result = requests.get(url=request_options.url,
                                  headers=request_options.headers,
                                  auth=request_options.auth)
        return result

    def add_query(self, query, result_object=None):
        self.__queries.append(query)
        if result_object is not None:
            self.__resultObjects[query] = result_object

    def before_execute_query(self, event):
        self.__events_list['BeforeExecuteQuery'] = event

    def after_execute_query(self, event):
        self.__events_list['AfterExecuteQuery'] = event

    @staticmethod
    def validate_response(response):
        try:
            response.raise_for_status()
        except HTTPError as e:
            raise ClientRequestException(*e.args, response=e.response)
