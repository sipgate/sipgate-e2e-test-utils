import asyncio
from datetime import timedelta
from typing import Callable, Any


async def wait_for_condition(
        condition: Callable[[], bool], attempts: int = 5, interval: timedelta = timedelta(milliseconds=100)) -> None:
    if attempts < 1:
        raise ValueError('needs at least one attempt')

    if interval < timedelta(milliseconds=0):
        raise ValueError('interval cannot be negative')

    attempt = 1
    while condition() is False:
        attempt += 1

        if attempt > attempts:
            raise TimeoutError('timed out waiting for condition')

        await asyncio.sleep(interval.total_seconds())


async def wait_for_assertions(
        asserter: Callable[[], Any], attempts: int = 5, interval: timedelta = timedelta(milliseconds=100)) -> None:
    if attempts < 1:
        raise ValueError('needs at least one attempt')

    if interval < timedelta(milliseconds=0):
        raise ValueError('interval cannot be negative')

    attempt = 1
    while True:
        try:
            asserter()
        except AssertionError as e:
            attempt += 1

            if attempt > attempts:
                raise e

            await asyncio.sleep(interval.total_seconds())
        else:
            return
