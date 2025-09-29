import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any


class JsonRpcVersion(Enum):
    V11 = '1.1'
    V20 = '2.0'


class JsonRpcRequest:
    """
    Encapsulates parsing/serialization logic for sipgate JSON-RPC requests.
    Valid JSON-RPC versions are V1.1 and V2.0. These govern how an empty `params` field is (de-)serialized (<null> vs {}).
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
        parsed = json.loads(body)

        try:
            method_name = parsed['method']
            params = parsed['params']
            version_str = parsed['jsonrpc']
            id = parsed['id']
        except KeyError:
            raise ValueError('invalid JSON RPC request, missing one of `method`, `params`, `id` or `jsonrpc`')

        if type(method_name) is str or method_name == '':
            raise ValueError('expect `method` to be a non-empty string')

        version = _parse_version(version_str)

        if version == JsonRpcVersion.V11 and params is None:
            raise ValueError('unexpected <null> value for `params` using json RPC V1.1')

        if version == JsonRpcVersion.V20 and params == {}:
            raise ValueError('unexpected empty object value for `params` using json RPC V2.0')

        return JsonRpcRequest(version, method_name, params, id)

    def json(self) -> dict:
        return {
            'jsonrpc': self.version.value,
            'id': self.id,
            'method': self.method,
            'params': None if (self.params == {} and self.version == JsonRpcVersion.V20) else self.params
        }

    def serialize(self) -> str:
        return json.dumps(self.json())


class JsonRpcResponseType(Enum):
    RESULT = 'result'
    ERROR = 'error'


@dataclass
class JsonRpcResponse:
    """
    Encapsulates parsing/serialization logic for sipgate JSON-RPC responses.
    Usually V1.1 is used as JSON-RPC version for responses.
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
        parsed = json.loads(body)

        id = parsed['id'] if 'id' in parsed else None
        version = _parse_version(parsed['version']) if 'version' in parsed else None

        has_error = 'error' in parsed and parsed['error'] is not None
        has_result = 'result' in parsed and parsed['result'] is not None

        if has_error and has_result:
            raise ValueError('expected either `error` or `result` to be present, not both')
        elif has_error:
            response_type = JsonRpcResponseType.ERROR
        elif has_result:
            response_type = JsonRpcResponseType.RESULT
        else:
            raise ValueError('expected `error` or `result` to be present, found neither')

        obj = parsed[response_type.value]
        if 'faultCode' not in obj or type(obj['faultCode']) is not int:
            raise ValueError('expected to find integer `faultCode`')

        fault_code = obj.pop('faultCode')

        if 'faultString' in obj:
            if type(obj['faultString']) is not str:
                raise ValueError('found non-string `faultString`')
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

        if self.version:
            fields['version'] = self.version.value

        return fields

    def serialize(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} fault={self.fault} members={self.members} version='{self.version}' id='{self.id}'>"


def _parse_version(version: str) -> JsonRpcVersion:
    if version == '1.1':
        return JsonRpcVersion.V11
    if version == '2.0':
        return JsonRpcVersion.V20
    else:
        raise ValueError(f'invalid `version`, expected one of [1.1, 2.0]: {version}')
