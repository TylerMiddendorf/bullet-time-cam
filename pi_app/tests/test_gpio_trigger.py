import unittest

from pi_app.bullettime.gpio_trigger import HardwareTrigger


class FakeBackend:
    def __init__(self):
        self.events = []

    def claim_output(self, pin, initial):
        self.events.append(("claim", pin, initial))

    def write(self, pin, level):
        self.events.append(("write", pin, level))

    def close(self, pin):
        self.events.append(("close", pin))


class TriggerTests(unittest.TestCase):
    def make_trigger(self, sleep=None):
        backend = FakeBackend()
        delays = []
        trigger = HardwareTrigger(17, 0.1, backend=backend, sleep=sleep or delays.append)
        return trigger, backend, delays

    def test_initialization_claims_output_low(self):
        trigger, backend, _ = self.make_trigger()
        self.assertEqual(backend.events, [("claim", 17, 0), ("write", 17, 0)])
        trigger.close()

    def test_one_pulse_is_low_high_low_for_100_ms(self):
        trigger, backend, delays = self.make_trigger()
        trigger.pulse()
        self.assertEqual(delays, [0.1])
        self.assertEqual(backend.events[-2:], [("write", 17, 1), ("write", 17, 0)])
        trigger.close()

    def test_repeated_pulses_each_return_low(self):
        trigger, backend, delays = self.make_trigger()
        trigger.pulse()
        trigger.pulse()
        self.assertEqual(delays, [0.1, 0.1])
        self.assertEqual(
            backend.events[2:],
            [
                ("write", 17, 1), ("write", 17, 0),
                ("write", 17, 1), ("write", 17, 0),
            ],
        )
        trigger.close()

    def test_exception_during_pulse_and_context_cleanup_leave_low(self):
        backend = FakeBackend()

        def fail_sleep(_seconds):
            raise RuntimeError("simulated application failure")

        with self.assertRaises(RuntimeError):
            with HardwareTrigger(17, 0.1, backend=backend, sleep=fail_sleep) as trigger:
                trigger.pulse()
        self.assertEqual(
            backend.events,
            [
                ("claim", 17, 0),
                ("write", 17, 0),
                ("write", 17, 1),
                ("write", 17, 0),
                ("write", 17, 0),
                ("close", 17),
            ],
        )


if __name__ == "__main__":
    unittest.main()
