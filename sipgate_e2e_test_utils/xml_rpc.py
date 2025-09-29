import base64
from dataclasses import dataclass, field
from typing import Any, Callable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


@dataclass
class XmlRpcRequest:
    """
    types not implemented (as not widely used for requests):
    - double
    - datetime.iso8601
    """

    method_name: str
    members: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} methodName='{self.method_name}' members={self.members}>"

    @staticmethod
    def parse(body: str | bytes) -> 'XmlRpcRequest':
        return _parse_xml_rpc_request(body)

    def serialize(self) -> str:
        return _serialize_xml_rpc_request(self)


@dataclass
class XmlRpcResponse:
    """
    types not implemented (as not widely used for responses):
    - double
    - datetime.iso8601
    """
    fault: tuple[int, str]
    members: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} fault={self.fault} members={self.members}>"

    @staticmethod
    def parse(body: str | bytes) -> 'XmlRpcResponse':
        return _parse_xml_rpc_response(body)

    def serialize(self) -> str:
        return _serialize_xml_rpc_response(self)


def _parse_xml_rpc_request(body: str | bytes) -> XmlRpcRequest:
    root = ElementTree.fromstring(body)
    if root.tag != 'methodCall':
        raise ValueError("Expecting root tag to be '<methodCall>'")

    method_name = root.find('methodName')
    if method_name is None or method_name.text is None:
        raise ValueError("Expected to find non-empty '<methodName>'")

    members = {}
    for member_node in root.findall('params/param/value/struct/member'):
        key, val = __parse_member(member_node)
        members[key] = val

    return XmlRpcRequest(method_name.text, members)


def _serialize_xml_rpc_request(request: XmlRpcRequest) -> str:
    root_param = '' if request.members == {} else f'<param><value>{__serialize_struct(request.members)}</value></param>'

    # TODO: omit whitespace?
    return f"""<?xml version="1.0"?>
        <methodCall>
            <methodName>{request.method_name}</methodName>
            <params>{root_param}</params>
        </methodCall>"""


def _parse_xml_rpc_response(body: str | bytes) -> XmlRpcResponse:
    root = ElementTree.fromstring(body)
    if root.tag != 'methodResponse':
        raise ValueError("Expecting root tag to be '<methodResponse>'")

    value = root.find('params/param/value/struct')
    if value is None:
        value = root.find('fault/value/struct')

    if value is None:
        raise ValueError("Expecting to find a value")

    members = __parse_struct(value)
    fault = (int(members.pop('faultCode')), str(members.pop('faultString')))
    return XmlRpcResponse(fault, members)


def _serialize_xml_rpc_response(response: XmlRpcResponse) -> str:
    (fault_code, fault_string) = response.fault
    params = dict(response.members, **{
        'faultCode': fault_code,
        'faultString': fault_string,
    })

    if fault_code == 200:
        wrapper = '<params><param><value>{}</value></param></params>'
    else:
        wrapper = '<fault><value>{}</value></fault>'

    return f"""<?xml version="1.0"?>
            <methodResponse>
                {wrapper.format(__serialize_struct(params))}
            </methodResponse>"""


def __parse_member(node: Element) -> tuple[str, Any]:
    assert node.tag == 'member', f"expected 'member', but got {node.tag=}"

    name_node = node.find('name')
    if name_node is None or name_node.text is None:
        raise ValueError("Expected to find non-empty '<member><name>'")

    value_node = node.find('value')
    if value_node is None:
        raise ValueError("Expected to find '<member><value>'")

    return name_node.text, __parse_value(value_node)


def __parse_value(node: Element) -> Any:
    assert node.tag == 'value', f"expected 'value', but got {node.tag=}"

    typed_value = node.find('*')
    if typed_value is None:
        # it is allowed to omit the <string></string> type
        return '' if node.text is None else node.text

    val_parsers: dict[str, Callable[[Element], Any]] = {
        'int': lambda n: int('' if n.text is None else n.text),
        'i4': lambda n: int('' if n.text is None else n.text),
        'boolean': lambda n: __parse_boolean(n.text),
        'string': lambda n: '' if n.text is None else n.text,
        'struct': lambda n: __parse_struct(n),
        'array': lambda n: __parse_array(n),
        'base64': lambda n: b'' if n.text is None else base64.b64decode(n.text),
    }

    try:
        parser = val_parsers[typed_value.tag]
    except KeyError:
        raise NotImplementedError(f"Unsupported type '<{typed_value.tag}>'")

    try:
        return parser(typed_value)
    except Exception:
        raise ValueError(f"Invalid value '{typed_value.text}' for <{typed_value.tag}>")


def __parse_boolean(text: str | None) -> bool:
    if text == '0':
        return False

    if text == '1':
        return True

    raise ValueError(f"expected '{text}' to be '0' or '1'")


def __parse_array(node: Element) -> list[Any]:
    assert node.tag == 'array', f"expected 'array', but got {node.tag=}"
    array_values = node.findall('data/value')

    return [__parse_value(struct_node) for struct_node in array_values]


def __parse_struct(node: Element) -> dict[str, Any]:
    assert node.tag == 'struct', f"expected 'struct', but got {node.tag=}"
    member_nodes = node.findall('member')

    return {k: v for k, v in map(__parse_member, member_nodes)}


def __serialize_struct(struct: dict[str, Any]) -> str:
    members = [__serialize_member(key, struct[key]) for key in struct]

    return f'<struct>{"\n".join(members)}</struct>'


def __serialize_array(array: list[Any]) -> str:
    values = [__serialize_value(val) for val in array]

    return f'<array><data>{"\n".join(values)}</data></array>'


def __serialize_member(name: str, value: Any) -> str:
    if value is None:
        return ''  # TODO: test

    return f"<member><name>{name}</name>{__serialize_value(value)}</member>"


def __serialize_value(value: Any) -> str:
    val_mappers: dict[type, Callable[[Any], str]] = {
        int: lambda val: f'<i4>{val}</i4>',
        str: lambda val: f'<string>{val}</string>',
        bool: lambda val: f'<boolean>{val}</boolean>',
        dict: lambda val: __serialize_struct(value),
        list: lambda val: __serialize_array(value)
    }

    try:
        val_mapper = val_mappers[type(value)]
    except KeyError:
        raise NotImplementedError(f'unsupported data type ({type(value)}) when serializing {value}')

    return f"<value>{val_mapper(value)}</value>"
