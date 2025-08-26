import json

from http_request_recorder import RecordedRequest


from unittest import TestCase
from sipgate_e2e_test_utils.rpc_matchers import xml_rpc, json_rpc


class TestSipgateRpcMatchers(TestCase):
    def test_xml_rpc(self) -> None:
        assertions = [
            (False, ('POST', '/jsonrpc', json.dumps({'method': 'test_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
            (False, ('POST', '/jsonrpc', b'<?xml version="1.0"?><methodCall><methodName>test_method</methodName><params><param><value></value></param></params></methodCall>')),
            (False, ('GET', '/rpc2', b'<?xml version="1.0"?><methodCall><methodName>test_method</methodName><params><param><value></value></param></params></methodCall>')),
            (False, ('POST', '/rpc2', b'anydata')),
            (False, ('POST', '/rpc2', b'<?xml version="1.0"?><methodCall><methodName>another_method</methodName><params><param><value></value></param></params></methodCall>')),
            (True, ('POST', '/rpc2', b'<?xml version="1.0"?><methodCall><methodName>test_method</methodName><params><param><value></value></param></params></methodCall>')),
            (True, ('POST', '/RPC2', b'<?xml version="1.0"?><methodCall><methodName>test_method</methodName><params><param><value></value></param></params></methodCall>')),
        ]

        for (expected, (method, path, body)) in assertions:
            with self.subTest(f'expect {expected} for method={method} path={path} body={body.decode()}'):
                request = RecordedRequest()
                request.method = method
                request.path = path
                request.body = body

                self.assertEqual(expected, xml_rpc('test_method')(request))

    def test_json_rpc(self) -> None:
        assertions = [
            (False, ('POST', '/rpc2', b'<?xml version="1.0"?><methodCall><methodName>test_method</methodName><params><param><value></value></param></params></methodCall>')),
            (False, ('POST', '/rpc2', json.dumps({'method': 'test_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
            (False, ('GET', '/jsonrpc', json.dumps({'method': 'test_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
            (False, ('POST', '/jsonrpc', b'anydata')),
            (False, ('POST', '/jsonrpc', json.dumps({'method': 'another_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
            (True, ('POST', '/jsonrpc', json.dumps({'method': 'test_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
            (True, ('POST', '/JSONRPC', json.dumps({'method': 'test_method', 'version': '1.1', 'params': [], 'id': 42}).encode())),
        ]

        for (expected, (method, path, body)) in assertions:
            with self.subTest(f'expect {expected} for method={method} path={path} body={body.decode()}'):
                request = RecordedRequest()
                request.method = method
                request.path = path
                request.body = body

                self.assertEqual(expected, json_rpc('test_method')(request))
