import json
from unittest import TestCase

from sipgate_e2e_test_utils.json_rpc import JsonRpcRequest, JsonRpcVersion


class TestJsonRpcRequest(TestCase):
    def test_parse_fails_empty_body(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse('')

    def test_parse_fails_non_json_body(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse('<methodCall></methodCall>')

    def test_parse_fails_missing_version(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'id': '42',
                'method': 'a_method_name',
                'params': {}
            }))

    def test_parse_fails_invalid_version(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '4.2',
                'id': '42',
                'method': 'a_method_name',
                'params': {}
            }))

    def test_parse_fails_missing_id(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'method': 'a_method_name',
                'params': {}
            }))

    def test_parse_fails_missing_method_name(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'id': '42',
                'params': {}
            }))

    def test_parse_fails_empty_method_name(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'id': '42',
                'method': '',
                'params': {}
            }))

    def test_parse_fails_non_string_method_name(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'id': '42',
                'method': 123,
                'params': {}
            }))

    def test_parse_fails_missing_params(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'id': '42',
            }))

    def test_parse_fails_empty_params_1_1(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '1.1',
                'id': '42',
                'method': 'a_method_name',
                'params': None
            }))

    def test_parse_succeeds_empty_params_1_1(self):
        request = JsonRpcRequest.parse(json.dumps({
            'jsonrpc': '1.1',
            'id': '42',
            'method': 'a_method_name',
            'params': {}
        }))

        self.assertEqual(JsonRpcVersion.V11, request.version)
        self.assertEqual('42', request.id)
        self.assertEqual('a_method_name', request.method)
        self.assertEqual({}, request.params)

    def test_parse_fails_empty_params_2_0(self):
        with self.assertRaises(ValueError):
            JsonRpcRequest.parse(json.dumps({
                'jsonrpc': '2.0',
                'id': '42',
                'method': 'a_method_name',
                'params': {}
            }))

    def test_parse_succeeds_empty_params_2_0(self):
        request = JsonRpcRequest.parse(json.dumps({
            'jsonrpc': '2.0',
            'id': '42',
            'method': 'a_method_name',
            'params': None
        }))

        self.assertEqual(JsonRpcVersion.V20, request.version)
        self.assertEqual('42', request.id)
        self.assertEqual('a_method_name', request.method)
        self.assertEqual({}, request.params)

    def test_parse_succeeds_with_params(self):
        request = JsonRpcRequest.parse(json.dumps({
            'jsonrpc': '2.0',
            'id': 'a_random_id',
            'method': 'a_method_name',
            'params': {
                'a_string': 'the_string_value',
                'a_boolean': True,
                'a_number': 42
            }
        }))

        self.assertEqual(JsonRpcVersion.V20, request.version)
        self.assertEqual('a_random_id', request.id)
        self.assertEqual('a_method_name', request.method)
        self.assertEqual('the_string_value', request.params['a_string'])
        self.assertEqual(True, request.params['a_boolean'])
        self.assertEqual(42, request.params['a_number'])

    def test_to_json_empty_params_1_1(self):
        request = JsonRpcRequest(JsonRpcVersion.V11, 'a_method_name')
        self.assertEqual({}, request.json()['params'])

    def test_to_json_empty_params_2_0(self):
        request = JsonRpcRequest(JsonRpcVersion.V20, 'a_method_name')
        self.assertEqual(None, request.json()['params'])

    def test_to_json(self):
        request = JsonRpcRequest(JsonRpcVersion.V20, 'a_method_name', {
            'a_string': 'the_string_value',
            'a_boolean': True,
            'a_number': 42
        }, id='an_id')

        self.assertEqual({
            'jsonrpc': '2.0',
            'id': 'an_id',
            'method': 'a_method_name',
            'params': {
                'a_string': 'the_string_value',
                'a_boolean': True,
                'a_number': 42
            }
        }, request.json())
