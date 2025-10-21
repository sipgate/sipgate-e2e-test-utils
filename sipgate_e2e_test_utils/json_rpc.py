import json
import uuid
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError
from typing import Any


class ParseError(SyntaxError):
    """An error when parsing a JSON-RPC body."""
    pass


class JsonRpcVersion(Enum):
    """Valid JSON-RPC versions."""
    V11 = '1.1'
    V20 = '2.0'


class JsonRpcRequest:
    """
    Encapsulates parsing/serialization logic for sipgate JSON-RPC requests.
    The request version governs how an empty `params` field is (de-)serialized (<null> for V1.1 vs {} for V2.0).
    When using the RpcRequest in python code, the empty `params` field will always be {} to enable simpler test assertions.
    """

    version: JsonRpcVersion
    method: str
    params: dict[str, Any]
    id: str

    def __init__(self, version: JsonRpcVersion, method: str, params=None, id=None):
        self.version = version
        self.method = method
        self.id = str(uuid.uuid4()) if id is None else id
        self.params = {} if params is None else params

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} method='{self.method}' params={self.params} version='{self.version}' id='{self.id}'>"

    @staticmethod
    def parse(body: str | bytes) -> 'JsonRpcRequest':
        try:
            json_body = json.loads(body)
        except JSONDecodeError:
            raise ParseError(f'{body=} must be valid JSON')

        try:
            method_name = json_body['method']
            params = json_body['params']
            id = json_body['id']
        except KeyError:
            raise ParseError(f'{body=} must contain keys `method`, `params` and `id`')

        if type(method_name) is not str or method_name == '':
            raise ParseError(f'{method_name=} must be non-empty string')

        version = _parse_request_version(json_body)

        if version == JsonRpcVersion.V11 and params is None:
            raise ParseError(f'{params=} must NOT be <null> when using JSON-RPC V1.1')

        if version == JsonRpcVersion.V20 and params == {}:
            raise ParseError(f'{params=} must NOT be an empty object when using JSON-RPC V2.0')

        return JsonRpcRequest(version, method_name, params, id)

    def json(self) -> dict:
        fields = {
            'id': self.id,
            'method': self.method,
            'params': None if (self.params == {} and self.version == JsonRpcVersion.V20) else self.params
        }

        if self.version == JsonRpcVersion.V11:
            fields['version'] = self.version.value
        elif self.version == JsonRpcVersion.V20:
            fields['jsonrpc'] = self.version.value

        return fields

    def serialize(self) -> str:
        return json.dumps(self.json())


class JsonRpcResponseType(Enum):
    RESULT = 'result'
    ERROR = 'error'


@dataclass
class JsonRpcResponse:
    """
    Encapsulates parsing/serialization logic for sipgate JSON-RPC responses.
    Usually V1.1 is used as JSON-RPC version for responses, but it is sometimes omitted.
    When using the RpcResponse in python code, an empty `result` field will always be {} (therefore excluding `faultCode` and `faultString`) to enable simpler test assertions.
    It is recommended, to use the result() and error() methods to ensure construction of valid responses.
    """

    type: JsonRpcResponseType
    fault: tuple[int, str]
    members: dict[str, Any]
    version: JsonRpcVersion | None
    id: str | None

    @staticmethod
    def result(fault_code: int, fault_string: str, members: dict[str, Any] | None = None, version: JsonRpcVersion | None = None, id: str | None = None) -> 'JsonRpcResponse':
        return JsonRpcResponse(JsonRpcResponseType.RESULT, (fault_code, fault_string), members if members else {}, version, id)

    @staticmethod
    def error(fault_code: int, fault_string: str, version: JsonRpcVersion | None = None, id: str | None = None) -> 'JsonRpcResponse':
        return JsonRpcResponse(JsonRpcResponseType.ERROR, (fault_code, fault_string), {}, version, id)

    @staticmethod
    def parse(body: str | bytes) -> 'JsonRpcResponse':
        try:
            parsed_body = json.loads(body)
        except JSONDecodeError:
            raise ParseError(f'{body=} must be valid JSON')

        id = parsed_body['id'] if 'id' in parsed_body else None
        version = _parse_response_version(parsed_body)

        has_error = 'error' in parsed_body and parsed_body['error'] is not None
        has_result = 'result' in parsed_body and parsed_body['result'] is not None

        if has_error and has_result:
            raise ParseError(f'{body=} must contain either `error` or `result`, found both')
        elif has_error:
            response_type = JsonRpcResponseType.ERROR
        elif has_result:
            response_type = JsonRpcResponseType.RESULT
        else:
            raise ParseError(f'{body=} must contain either `error` or `result`, found neither')

        obj = parsed_body[response_type.value]
        if 'faultCode' not in obj or type(obj['faultCode']) is not int:
            raise ParseError(f'{body=} must contain int `faultCode`')

        fault_code = obj.pop('faultCode')

        if 'faultString' in obj:
            if type(obj['faultString']) is not str:
                raise ParseError(f'{body=} must contain string `faultString`')
            fault_string = obj.pop('faultString')
        else:
            fault_string = ''

        return JsonRpcResponse(response_type, (fault_code, fault_string), obj, version, id)

    def json(self) -> dict:
        (fault_code, fault_string) = self.fault
        fields: dict[str, Any] = {
            self.type.value: {
                'faultCode': fault_code,
                'faultString': fault_string,
                **self.members
            },
            (JsonRpcResponseType.ERROR.value if self.type == JsonRpcResponseType.RESULT else JsonRpcResponseType.RESULT.value): None
        }

        if self.id:
            fields['id'] = self.id

        if self.version == JsonRpcVersion.V11:
            fields['version'] = self.version.value
        elif self.version == JsonRpcVersion.V20:
            fields['jsonrpc'] = self.version.value

        return fields

    def serialize(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} fault={self.fault} members={self.members} version='{self.version}' id='{self.id}'>"


def _parse_request_version(json_body: dict[str, Any]) -> JsonRpcVersion:
    has_jsonrpc_field = 'jsonrpc' in json_body
    has_version_field = 'version' in json_body

    if has_jsonrpc_field and has_version_field:
        raise ParseError(f'{json_body=} must either contain `jsonrpc=2.0` or `version=1.1`')
    elif has_version_field and json_body['version'] == '1.1':
        return JsonRpcVersion.V11
    elif has_jsonrpc_field and json_body['jsonrpc'] == '2.0':
        return JsonRpcVersion.V20
    else:
        raise ParseError(f'{json_body=} must either contain `jsonrpc=2.0` or `version=1.1`')


def _parse_response_version(json_body: dict[str, Any]) -> JsonRpcVersion | None:
    has_jsonrpc_field = 'jsonrpc' in json_body
    has_version_field = 'version' in json_body

    if not has_version_field and not has_jsonrpc_field:
        return None
    elif has_jsonrpc_field and has_version_field:
        raise ParseError(f'{json_body=} must either contain `jsonrpc=2.0` or `version=1.1` or neither of those')
    elif has_version_field and json_body['version'] == '1.1':
        return JsonRpcVersion.V11
    elif has_jsonrpc_field and json_body['jsonrpc'] == '2.0':
        return JsonRpcVersion.V20
    else:
        raise ParseError(f'{json_body=} must either contain `jsonrpc=2.0` or `version=1.1` or neither of those')
