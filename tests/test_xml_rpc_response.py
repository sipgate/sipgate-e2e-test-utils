from unittest import TestCase
from xml.etree.ElementTree import ParseError

from sipgate_e2e_test_utils.xml_rpc import XmlRpcResponse, XmlRpcResponseType


class TestSipgateXmlRpcResponse(TestCase):
    def test_construct_empty_result(self):
        response = XmlRpcResponse.result(200, 'OK')

        self.assertEqual(XmlRpcResponseType.RESULT, response.type)
        self.assertEqual((200, 'OK'), response.fault)
        self.assertEqual({}, response.members)

    def test_construct_result(self):
        response = XmlRpcResponse.result(413, 'A BIT OKAY', {
            'a_param': 42
        })

        self.assertEqual(XmlRpcResponseType.RESULT, response.type)
        self.assertEqual((413, 'A BIT OKAY'), response.fault)
        self.assertEqual({
            'a_param': 42
        }, response.members)

    def test_construct_error(self):
        response = XmlRpcResponse.error(500, 'NOT OK')

        self.assertEqual(XmlRpcResponseType.ERROR, response.type)
        self.assertEqual((500, 'NOT OK'), response.fault)
        self.assertEqual({}, response.members)

    def test_empty_body(self):
        with self.assertRaises(ParseError):
            XmlRpcResponse.parse('')

    def test_parse_non_xml_body(self):
        with self.assertRaises(ParseError):
            XmlRpcResponse.parse("{'key': 'value'}")

    def test_parse_invalid_body(self):
        body = """<?xml version="1.0" encoding="UTF-8"?>
            <methodCall>
                <methodName>another_method_name</methodName>
                <params><param><value>
                    <struct>
                        <member><name>TNB</name><value><string>D111</string></value></member>
                    </struct>
                </value></param></params>
            </methodCall>"""

        with self.assertRaises(ValueError):
            XmlRpcResponse.parse(body)

    def test_parse_complex_success(self):
        body = """<?xml version="1.0"?>
            <methodResponse>
                <params>
                    <param><value>
                        <struct>
                            <member><name>empty_string</name><value><string></string></value></member>
                            <member><name>tnb</name><value><string>D146</string></value></member>
                            <member><name>bool_true</name><value><boolean>1</boolean></value></member>
                            <member><name>bool_false</name><value><boolean>0</boolean></value></member>
                            <member>
                                <name>the_data</name>
                                <value><struct>
                                    <member><name>date</name><value><string>2025-02-01</string></value></member>
                                </struct></value>
                            </member>
                            <member>
                                <name>blocks</name>
                                <value><array>
                                    <data>
                                        <value><struct>
                                            <member><name>number</name><value><string>0555</string></value></member>
                                        </struct></value>
                                        <value><struct>
                                            <member><name>number</name><value><string>0777</string></value></member>
                                        </struct></value>
                                    </data>
                                </array></value>
                            </member>
                            <member><name>faultString</name><value><string>OK</string></value></member>
                            <member><name>faultCode</name><value><i4>200</i4></value></member>
                        </struct>
                    </value></param>
                </params>
            </methodResponse>"""

        parsed = XmlRpcResponse.parse(body)

        self.assertEqual((200, 'OK'), parsed.fault)

        self.assertEqual('', parsed.members['empty_string'])
        self.assertEqual('D146', parsed.members['tnb'])
        self.assertTrue(parsed.members['bool_true'])
        self.assertFalse(parsed.members['bool_false'])
        self.assertEqual({
            'date': '2025-02-01'
        }, parsed.members['the_data'])
        self.assertEqual([{
            'number': '0555',
        }, {
            'number': '0777',
        }], parsed.members['blocks'])

    def test_parse_complex_error(self):
        body = """<?xml version="1.0"?>
            <methodResponse>
                    <fault><value>
                        <struct>
                            <member>
                                <name>things_that_went_wrong</name>
                                <value><array>
                                    <data>
                                        <value><string>one</string></value>
                                        <value><string>two</string></value>
                                    </data>
                                </array></value>
                            </member>
                            <member><name>faultString</name><value><string>NOT_OK</string></value></member>
                            <member><name>faultCode</name><value><i4>423</i4></value></member>
                        </struct>
                    </value></fault>
            </methodResponse>"""

        parsed = XmlRpcResponse.parse(body)
        self.assertEqual((423, 'NOT_OK'), parsed.fault)
        self.assertTrue(['one', 'two'], parsed.members['things_that_went_wrong'])

    def test_parse_invalid_members(self):
        members = [
            {'name': 'bool_empty', 'value': '<boolean></boolean>'},
            {'name': 'bool_string', 'value': '<boolean>true</boolean>'},
            {'name': 'int_text', 'value': '<int>fortytwo</int>'},
            {'name': 'int_empty', 'value': '<i4></i4>'}
        ]

        for member in members:
            with self.subTest(member['name']):
                body = f"""<?xml version="1.0"?>
                    <methodResponse>
                        <params><param><value>
                            <struct>
                                <member><name>{member['name']}</name><value>{member['value']}</value></member>
                            </struct>
                        </value></param></params>
                    </methodResponse>"""

                with self.assertRaises(ValueError):
                    XmlRpcResponse.parse(body)

    def test_string_representation(self):
        body = """<?xml version="1.0"?>
                    <methodResponse>
                        <params>
                            <param><value>
                                <struct>
                                    <member><name>faultString</name><value><string>OK</string></value></member>
                                    <member><name>faultCode</name><value><i4>200</i4></value></member>
                                </struct>
                            </value></param>
                        </params>
                    </methodResponse>"""

        parsed = XmlRpcResponse.parse(body)
        self.assertRegex(f"{parsed}", '^<XmlRpcResponse.*fault.*200.*OK.*>$')

    def test_serialization_success_response(self):
        response = XmlRpcResponse.result(200, 'OK')

        expected_body = """<?xml version="1.0"?>
            <methodResponse>
                <params>
                    <param><value>
                        <struct>
                            <member><name>faultCode</name><value><i4>200</i4></value></member>
                            <member><name>faultString</name><value><string>OK</string></value></member>
                        </struct>
                    </value></param>
                </params>
            </methodResponse>"""

        # TODO: use better comparison
        #  this would ignore spaces in values and does not ignore order of params
        self.assertEqual(''.join(expected_body.split()), ''.join(response.serialize().split()))

    def test_serialization_error_response(self):
        response = XmlRpcResponse.error(407, 'NOT SO OKAY')

        expected_body = """<?xml version="1.0"?>
            <methodResponse>
                <fault><value>
                    <struct>
                        <member><name>faultCode</name><value><i4>407</i4></value></member>
                        <member><name>faultString</name><value><string>NOT SO OKAY</string></value></member>
                    </struct>
                </value></fault>
            </methodResponse>"""

        # TODO: use better comparison
        #  this would ignore spaces in values and does not ignore order of params
        self.assertEqual(''.join(expected_body.split()), ''.join(response.serialize().split()))

    def test_serialization_members(self):
        response = XmlRpcResponse.result(401, 'NOT QUITE OK', {
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
            <methodResponse>
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
                        <member><name>faultCode</name><value><i4>401</i4></value></member>
                        <member><name>faultString</name><value><string>NOT QUITE OK</string></value></member>
                    </struct>
                </value></param></params>
            </methodResponse>"""

        # TODO: use better comparison
        #  this would ignore spaces in values and does not ignore order of params
        self.assertEqual(''.join(expected_body.split()), ''.join(response.serialize().split()))
