import unittest

from sipgate_e2e_test_utils.waiting import wait_for_assertions


class TestWaitForAssertions(unittest.IsolatedAsyncioTestCase):
    async def test_completes_when_assertion_succeeds(self) -> None:
        await wait_for_assertions(lambda: self.assertEqual(1, 1))

    async def test_completes_when_assertion_succeeds_async(self) -> None:
        async def asserter():
            self.assertEqual(1, 1)

        await wait_for_assertions(asserter, attempts=3)

    async def test_fails_on_exception(self) -> None:
        def raiser():
            raise ValueError()

        with self.assertRaises(ValueError):
            await wait_for_assertions(raiser, attempts=3)

    async def test_fails_on_exception_async(self) -> None:
        async def raiser():
            raise ValueError()

        with self.assertRaises(ValueError):
            await wait_for_assertions(raiser, attempts=3)

    async def test_throws_after_num_attempts_when_assertion_fails(self) -> None:
        attempts_done = 0

        def asserter() -> None:
            nonlocal attempts_done
            attempts_done += 1

            self.assertEqual(1, 2)

        with self.assertRaises(AssertionError):
            await wait_for_assertions(asserter, attempts=3)

        self.assertEqual(3, attempts_done)

    async def test_throws_after_num_attempts_when_assertion_fails_async(self) -> None:
        attempts_done = 0

        async def asserter() -> None:
            nonlocal attempts_done
            attempts_done += 1

            self.assertEqual(1, 2)

        with self.assertRaises(AssertionError):
            await wait_for_assertions(asserter, attempts=3)

        self.assertEqual(3, attempts_done)
