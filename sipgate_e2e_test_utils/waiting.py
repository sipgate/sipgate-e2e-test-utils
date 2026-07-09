import asyncio
import inspect
from datetime import timedelta
from typing import Callable, Awaitable


async def wait_for_condition(
        condition: Callable[[], bool | Awaitable[bool]], attempts: int = 5, interval: timedelta = timedelta(milliseconds=100)) -> None:
    if attempts < 1:
        raise ValueError('needs at least one attempt')

    if interval < timedelta(milliseconds=0):
        raise ValueError('interval cannot be negative')

    attempt = 1

    async def check_condition() -> bool:
        if inspect.iscoroutinefunction(condition):
            return await condition()
        else:
            return condition()

    while await check_condition() is False:
        attempt += 1

        if attempt > attempts:
            raise TimeoutError('timed out waiting for condition')

        await asyncio.sleep(interval.total_seconds())


async def wait_for_assertions(
        asserter: Callable[[], None | Awaitable[None]], attempts: int = 5, interval: timedelta = timedelta(milliseconds=100)) -> None:
    if attempts < 1:
        raise ValueError('needs at least one attempt')

    if interval < timedelta(milliseconds=0):
        raise ValueError('interval cannot be negative')

    attempt = 1
    while True:
        try:
            if inspect.iscoroutinefunction(asserter):
                await asserter()
            else:
                asserter()
        except AssertionError as e:
            attempt += 1

            if attempt > attempts:
                raise e

            await asyncio.sleep(interval.total_seconds())
        else:
            return
