import unittest

from sipgate_e2e_test_utils.waiting import wait_for_condition


class TestWaitForCondition(unittest.IsolatedAsyncioTestCase):
    async def test_completes_when_condition_is_met(self) -> None:
        await wait_for_condition(lambda: True)

    async def test_completes_when_condition_is_met_async(self) -> None:
        async def waiter():
            return True

        await wait_for_condition(waiter)

    async def test_fails_on_exception(self) -> None:
        def raiser():
            raise ValueError()

        with self.assertRaises(ValueError):
            await wait_for_condition(raiser, attempts=3)

    async def test_fails_on_exception_async(self) -> None:
        async def raiser():
            raise ValueError()

        with self.assertRaises(ValueError):
            await wait_for_condition(raiser, attempts=3)

    async def test_throws_after_num_attempts_when_condition_is_not_met(self) -> None:
        attempts_done = 0

        def waiter() -> bool:
            nonlocal attempts_done
            attempts_done += 1
            return False

        with self.assertRaises(TimeoutError):
            await wait_for_condition(waiter, attempts=3)

        self.assertEqual(3, attempts_done)

    async def test_throws_after_num_attempts_when_condition_is_not_met_async(self) -> None:
        attempts_done = 0

        async def waiter() -> bool:
            nonlocal attempts_done
            attempts_done += 1
            return False

        with self.assertRaises(TimeoutError):
            await wait_for_condition(waiter, attempts=3)

        self.assertEqual(3, attempts_done)
