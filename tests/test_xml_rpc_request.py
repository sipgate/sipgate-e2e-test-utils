from unittest import TestCase
from xml.etree.ElementTree import ParseError

from sipgate_e2e_test_utils.xml_rpc import XmlRpcRequest


class TestSipgateXmlRpcRequest(TestCase):
    def test_empty_body(self) -> None:
        with self.assertRaises(ParseError):
            XmlRpcRequest.parse('')

    def test_non_xml_body(self) -> None:
        with self.assertRaises(ParseError):
            XmlRpcRequest.parse("{'key': 'value'}")

    def test_response_is_not_parsed_as_request(self) -> None:
        body = """<?xml version="1.0" encoding="UTF-8"?>
            <methodResponse>
                <params><param><value>
                    <struct>
                        <member><name>faultString</name><value><string>OK</string></value></member>
                        <member><name>faultCode</name><value><i4>200</i4></value></member>
                    </struct>
                </value></param></params>
            </methodResponse>"""

        with self.assertRaises(ValueError):
            XmlRpcRequest.parse(body)

    def test_method_name(self) -> None:
        body = """<?xml version="1.0"?>
                    <methodCall>
                        <methodName>a_method_name</methodName>
                        <params><param><value></value></param></params>
                    </methodCall>"""

        parsed = XmlRpcRequest.parse(body)
        self.assertEqual('a_method_name', parsed.method_name)

    def test_valid_members(self) -> None:
        body = """<?xml version="1.0"?>
            <methodCall>
                <methodName>a_method_name</methodName>
                <params><param><value>
                    <struct>
                        <member><name>TNB</name><value><string>D222</string></value></member>
                        <member><name>port_date</name><value><string>2025-01-01</string></value></member>
                        <member><name>emptyString</name><value><string></string></value></member>
                        <member><name>stringWithoutType</name><value>thisIsAlsoAString</value></member>
                        <member><name>bool_true</name><value><boolean>1</boolean></value></member>
                        <member><name>bool_false</name><value><boolean>0</boolean></value></member>
                        <member><name>i4</name><value><i4>-23</i4></value></member>
                        <member><name>int</name><value><int>42</int></value></member>
                        <member><name>base64_empty</name><value><base64></base64></value></member>
                        <member><name>base64_data</name><value><base64>YW55X2RhdGE=</base64></value></member>
                    </struct>
                </value></param></params>
            </methodCall>"""

        parsed = XmlRpcRequest.parse(body)
        self.assertEqual('D222', parsed.members['TNB'])
        self.assertEqual('2025-01-01', parsed.members['port_date'])
        self.assertEqual('', parsed.members['emptyString'])
        self.assertEqual('thisIsAlsoAString', parsed.members['stringWithoutType'])
        self.assertEqual(True, parsed.members['bool_true'])
        self.assertEqual(False, parsed.members['bool_false'])
        self.assertEqual(-23, parsed.members['i4'])
        self.assertEqual(42, parsed.members['int'])
        self.assertEqual(b'', parsed.members['base64_empty'])
        self.assertEqual(b'any_data', parsed.members['base64_data'])

    def test_invalid_members(self) -> None:
        members = [
            {'name': 'bool_empty', 'value': '<boolean></boolean>'},
            {'name': 'bool_string', 'value': '<boolean>true</boolean>'},
            {'name': 'int_text', 'value': '<int>fortytwo</int>'},
            {'name': 'int_empty', 'value': '<i4></i4>'}
        ]

        for member in members:
            with self.subTest(member['name']):
                body = f"""<?xml version="1.0"?>
                    <methodCall>
                        <methodName>a_method_name</methodName>
                        <params><param><value>
                            <struct>
                                <member><name>{member['name']}</name><value>{member['value']}</value></member>
                            </struct>
                        </value></param></params>
                    </methodCall>"""

                with self.assertRaises(ValueError):
                    XmlRpcRequest.parse(body)

    def test_unsupported_data_type(self) -> None:
        body = """<?xml version="1.0"?>
                    <methodCall>
                        <methodName>a_method_name</methodName>
                        <params><param><value>
                            <struct>
                                <member><name>PI</name><value><float>3.14</float></value></member>
                            </struct>
                        </value></param></params>
                    </methodCall>"""

        with self.assertRaises(NotImplementedError):
            XmlRpcRequest.parse(body)

    def test_has_string_representation(self) -> None:
        body = """<?xml version="1.0"?>
            <methodCall>
                <methodName>another_method_name</methodName>
                <params><param><value>
                    <struct>
                        <member><name>TNB</name><value><string>D111</string></value></member>
                    </struct>
                </value></param></params>
            </methodCall>"""

        parsed = XmlRpcRequest.parse(body)
        self.assertRegex(f"{parsed}", "^<XmlRpcRequest.*methodName='another_method_name'.*>$")
        self.assertIn('TNB', f"{parsed}")
        self.assertIn('D111', f"{parsed}")

    def test_also_accepts_bytes(self) -> None:
        body = b"""<?xml version="1.0"?>
                    <methodCall>
                        <methodName>a_method_name</methodName>
                        <params><param><value></value></param></params>
                    </methodCall>"""

        XmlRpcRequest.parse(body)

    def test_serialization_empty_request(self) -> None:
        request = XmlRpcRequest('a_method', {})

        expected_body = """<?xml version="1.0"?>
            <methodCall>
                <methodName>a_method</methodName>
                <params></params>
            </methodCall>"""

        # TODO: use better comparison, this would ignore spaces in values
        self.assertEqual(''.join(expected_body.split()), ''.join(request.serialize().split()))

    def test_serialization(self) -> None:
        request = XmlRpcRequest('a_method', {
            'an_int': 42,
            'a_string': 'the_value',
            'a_struct': {
                'another_int': 23
            },
            'an_array': [{
                'another_str': 'the_other_value'
            }]
        })

        expected_body = """<?xml version="1.0"?>
            <methodCall>
                <methodName>a_method</methodName>
                <params><param><value>
                    <struct>
                        <member><name>an_int</name><value><i4>42</i4></value></member>
                        <member><name>a_string</name><value><string>the_value</string></value></member>
                        <member><name>a_struct</name><value><struct>
                            <member><name>another_int</name><value><i4>23</i4></value></member>
                        </struct></value></member>
                        <member><name>an_array</name><value><array>
                            <data>
                                <value><struct>
                                    <member><name>another_str</name><value><string>the_other_value</string></value></member>
                                </struct></value>
                            </data>
                        </array></value></member>
                    </struct>
                </value></param></params>
            </methodCall>"""

        # TODO: use better comparison, this would ignore spaces in values
        self.assertEqual(''.join(expected_body.split()), ''.join(request.serialize().split()))
