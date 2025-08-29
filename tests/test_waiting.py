import unittest

from sipgate_e2e_test_utils.waiting import wait_for_condition, wait_for_assertions


class WaitingTest(unittest.IsolatedAsyncioTestCase):
    async def test_completes_when_condition_is_met(self) -> None:
        await wait_for_condition(lambda: True)

    async def test_throws_after_num_attempts_when_condition_is_not_met(self) -> None:
        attempts_done = 0

        def waiter() -> bool:
            nonlocal attempts_done
            attempts_done += 1
            return False

        with self.assertRaises(TimeoutError):
            await wait_for_condition(waiter, attempts=3)

        self.assertEqual(3, attempts_done)

    async def test_completes_when_assertion_succeeds(self) -> None:
        await wait_for_assertions(lambda: self.assertEqual(1, 1))

    async def test_throws_after_num_attempts_when_assertion_fails(self) -> None:
        attempts_done = 0

        def asserter() -> None:
            nonlocal attempts_done
            attempts_done += 1

            self.assertEqual(1, 2)

        with self.assertRaises(AssertionError):
            await wait_for_assertions(asserter, attempts=3)

        self.assertEqual(3, attempts_done)
