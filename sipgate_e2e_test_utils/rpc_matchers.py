import json
from typing import Callable

from http_request_recorder import RecordedRequest


def json_rpc(method: str) -> Callable[[RecordedRequest], bool]:
    def matcher(request: RecordedRequest) -> bool:
        if request.method != 'POST' or '/jsonrpc' != request.path.lower():
            return False

        try:
            parsed = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return False

        return 'method' in parsed and method == parsed['method']

    return matcher


def xml_rpc(method: str) -> Callable[[RecordedRequest], bool]:
    def matcher(request: RecordedRequest) -> bool:
        return (
            'POST' == request.method and
            '/rpc2' == request.path.lower() and
            b'<methodName>' + method.encode() + b'</methodName>' in request.body)

    return matcher
