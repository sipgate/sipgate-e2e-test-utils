import asyncio
import unittest
from asyncio import create_task

from aiohttp import web, ClientSession

from sipgate_e2e_test_utils.jobd import JobD

from sipgate_e2e_test_utils.xml_rpc import XmlRpcRequest, XmlRpcResponse


class TestJobD(unittest.IsolatedAsyncioTestCase):
    async def test_serves_functions_xml(self):
        any_port = 42
        async with (JobD('localhost', any_port), ClientSession() as http):
            response = await http.get('http://localhost:8777/functions.xml')

            self.assertIn('jobd.updateEvent', await response.text())

    async def test_returns_success(self):
        mock_service = MockService(46968)
        await mock_service.start()

        async with (JobD('localhost', mock_service.port) as jobd):
            job_result = await jobd.trigger_job_and_record_answer('any_job')

            self.assertIn(b'any_value', job_result)

        await mock_service.stop()


class MockService:
    def __init__(self, port: int) -> None:
        self.port = port

        app = web.Application()
        app.add_routes([web.post('/RPC2', self.__handle_request)])
        self.runner = web.AppRunner(app)

    async def start(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await site.start()

    async def __handle_request(self, request: web.BaseRequest) -> web.Response:
        xml_rpc_request = XmlRpcRequest.parse(await request.text())
        assert 'cron.triggerJob' == xml_rpc_request.method_name

        create_task(self.__send_result_to_jobd_after_some_time(xml_rpc_request.members['notificationUrl']))

        return web.Response(status=200, body=XmlRpcResponse.result(200, 'OK').serialize())

    async def __send_result_to_jobd_after_some_time(self, notification_url: str):
        await asyncio.sleep(0.25)

        async with ClientSession() as http:
            await http.post(notification_url, data=XmlRpcRequest('jobd.updateEvent', {
                'any_field': 'any_value'
            }).serialize())

    async def stop(self):
        await self.runner.cleanup()
