import os
from typing import Any

import aiohttp
import socket
from http_request_recorder import HttpRequestRecorder

from sipgate_e2e_test_utils.rpc_matchers import xml_rpc
from sipgate_e2e_test_utils.xml_rpc import XmlRpcRequest, XmlRpcResponse

with open(os.path.join(os.path.dirname(__file__), 'jobd_functions.xml')) as file:
    JOBD_FUNCTIONS_XML = file.read()


class JobD:
    def __init__(self, system_hostname: str, system_port: int) -> None:
        self.notification_url = f"http://{socket.gethostname()}:8777/RPC2"
        self.system_url = f"http://{system_hostname}:{system_port}/RPC2"

    async def __aenter__(self) -> "JobD":
        self.recorder = HttpRequestRecorder(name='JobD', port=8777)
        self.recorder.expect_path(path='/functions.xml',
                                  responses=(JOBD_FUNCTIONS_XML for _ in range(100)))

        self.session = aiohttp.ClientSession()

        await self.recorder.__aenter__()
        return self

    async def trigger_job_and_record_answer(self, job_name: str, timeout: int = 10) -> bytes:
        expectation = self.recorder.expect(
            xml_rpc('jobd.updateEvent'), responses=XmlRpcResponse(200, 'ok').serialize(), timeout=timeout)

        response = await self.session.post(self.system_url, data=XmlRpcRequest('cron.triggerJob', {
            'jobName': job_name,
            'notificationUrl': self.notification_url,
            'uniqueid': 42
        }).serialize())
        assert 200 == response.status

        recorded_request: bytes = await expectation.wait()
        return recorded_request

    async def __aexit__(self, *args: tuple[Any]) -> None:
        await self.session.close()
        await_aexit__: None = await self.recorder.__aexit__(*args)
        return await_aexit__
