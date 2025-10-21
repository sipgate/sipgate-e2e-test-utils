import json
from unittest import TestCase

from sipgate_e2e_test_utils.json_rpc import JsonRpcResponse, JsonRpcVersion, JsonRpcResponseType, ParseError


class TestJsonRpcResponse(TestCase):
    def test_construct_empty_result(self):
        response = JsonRpcResponse.result(200, 'OK')

        self.assertEqual(JsonRpcResponseType.RESULT, response.type)
        self.assertEqual((200, 'OK'), response.fault)
        self.assertEqual({}, response.members)
        self.assertIsNone(response.version)
        self.assertIsNone(response.id)

    def test_construct_result(self):
        response = JsonRpcResponse.result(413, 'A BIT OKAY', {
            'a_param': 42
        })

        self.assertEqual(JsonRpcResponseType.RESULT, response.type)
        self.assertEqual((413, 'A BIT OKAY'), response.fault)
        self.assertEqual({
            'a_param': 42
        }, response.members)
        self.assertIsNone(response.version)
        self.assertIsNone(response.id)

    def test_construct_error(self):
        response = JsonRpcResponse.error(500, 'NOT OK')

        self.assertEqual(JsonRpcResponseType.ERROR, response.type)
        self.assertEqual((500, 'NOT OK'), response.fault)
        self.assertEqual({}, response.members)
        self.assertIsNone(response.version)
        self.assertIsNone(response.id)

    def test_parse_fails_empty_body(self):
        with self.assertRaises(ParseError):
            JsonRpcResponse.parse('')

    def test_parse_fails_non_json_body(self):
        with self.assertRaises(ParseError):
            JsonRpcResponse.parse('not_json')

    def test_parse_fails_neither_result_or_error_present(self):
        with self.assertRaises(ParseError):
            JsonRpcResponse.parse(json.dumps({
                'id': '42',
            }))

    def test_parse_fails_invalid_version(self):
        invalid_versions = [{
            'version': '2.0',
        }, {
            'version': '1.4'
        }, {
            'jsonrpc': '1.1'
        }, {
            'jsonrpc': '4.2'
        }, {
            'version': '1.1',
            'jsonrpc': '2.0'
        }]

        for v in invalid_versions:
            with self.subTest(v):
                with self.assertRaises(ParseError):
                    JsonRpcResponse.parse(json.dumps({
                        **v,
                        'result': _fault(200, '')
                    }))

    def test_parse_fails_both_result_and_error_present(self):
        with self.assertRaises(ParseError):
            JsonRpcResponse.parse(json.dumps({
                'result': _fault(200, ''),
                'error': _fault(400, '')
            }))

    def test_parse_fails_no_fault_code_present(self):
        for response_type in ['result', 'error']:
            with (self.subTest(response_type), self.assertRaises(ParseError)):
                JsonRpcResponse.parse(json.dumps({
                    response_type: {},
                }))

    def test_parse_fails_non_int_fault_code_in_result(self):
        for response_type in ['result', 'error']:
            with (self.subTest(response_type), self.assertRaises(ParseError)):
                JsonRpcResponse.parse(json.dumps({
                    response_type: {
                        'faultCode': 'non_int'
                    },
                }))

    def test_parse_fails_non_string_fault_string(self):
        for response_type in ['result', 'error']:
            with (self.subTest(response_type), self.assertRaises(ParseError)):
                JsonRpcResponse.parse(json.dumps({
                    response_type: {
                        'faultCode': 200,
                        'faultString': 200
                    },
                }))

    def test_parse_success_minimum_viable_response(self):
        for response_type in [JsonRpcResponseType.RESULT, JsonRpcResponseType.ERROR]:
            with self.subTest(response_type.value):
                response = JsonRpcResponse.parse(json.dumps({
                    response_type.value: _fault(200, '')
                }))

                self.assertEqual(response_type, response.type)
                self.assertEqual((200, ''), response.fault)
                self.assertEqual({}, response.members)
                self.assertIsNone(response.version)
                self.assertIsNone(response.id)

    def test_parse_success_erroneous_response(self):
        response = JsonRpcResponse.parse(json.dumps({
            'version': '1.1',
            'id': 'any_id',
            'error': _fault(427, 'an error'),
            'result': None
        }))

        self.assertEqual(JsonRpcVersion.V11, response.version)
        self.assertEqual('any_id', response.id)
        self.assertEqual((427, 'an error'), response.fault)
        self.assertEqual({}, response.members)

    def test_parse_success_with_params(self):
        response = JsonRpcResponse.parse(json.dumps({
            'version': '1.1',
            'id': 'any_id',
            'result': {
                **_fault(200, ''),
                'a_string': 'the_string_value',
                'a_boolean': True,
                'a_number': 42
            },
            'error': None
        }))

        self.assertEqual(JsonRpcVersion.V11, response.version)
        self.assertEqual((200, ''), response.fault)
        self.assertEqual('any_id', response.id)
        self.assertEqual('the_string_value', response.members['a_string'])
        self.assertEqual(True, response.members['a_boolean'])
        self.assertEqual(42, response.members['a_number'])

    def test_to_json_error_response(self):
        request = JsonRpcResponse.error(400, 'an_error',  JsonRpcVersion.V11, 'an_id')

        self.assertDictEqual({
            'version': '1.1',
            'id': 'an_id',
            'error': {
                'faultCode': 400,
                'faultString': 'an_error',
            },
            'result': None
        }, request.json())

    def test_to_json_success_response(self):
        request = JsonRpcResponse.result(200, '',  {
            'a_string': 'the_string_value',
            'a_boolean': True,
            'a_number': 42
        }, JsonRpcVersion.V11, 'an_id')

        self.assertDictEqual({
            'version': '1.1',
            'id': 'an_id',
            'result': {
                'faultCode': 200,
                'faultString': '',
                'a_string': 'the_string_value',
                'a_boolean': True,
                'a_number': 42
            },
            'error': None
        }, request.json())


def _fault(code: int, string: str):
    return {
        'faultCode': code,
        'faultString': string
    }
