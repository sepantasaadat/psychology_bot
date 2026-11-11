import unittest
import jdatetime
import main

class TestCancellationPolicyHelpers(unittest.TestCase):
    def test_parse_appointment_datetime(self):
        dt = main.parse_appointment_datetime("1405/08/25", "18:30")
        self.assertEqual(dt.year, 1405)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 25)
        self.assertEqual(dt.hour, 18)
        self.assertEqual(dt.minute, 30)

    def test_can_cancel_appointment_eligibility(self):
        # Simulated "now": 1405/08/20 at 18:00
        ref_now = jdatetime.datetime(1405, 8, 20, 18, 0)

        # 1. 72 hours away: eligible
        eligible, reason = main.can_cancel_appointment("1405/08/23", "18:00", now=ref_now)
        self.assertTrue(eligible)
        self.assertEqual(reason, "ok")

        # 2. Exactly 48 hours away: eligible
        eligible, reason = main.can_cancel_appointment("1405/08/22", "18:00", now=ref_now)
        self.assertTrue(eligible)
        self.assertEqual(reason, "ok")

        # 3. 47 hours away: within 48 hours, ineligible
        eligible, reason = main.can_cancel_appointment("1405/08/22", "17:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "within_48_hours")

        # 4. Same day, 2 hours away: within 48 hours, ineligible
        eligible, reason = main.can_cancel_appointment("1405/08/20", "20:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "within_48_hours")

        # 5. Exactly now (0 hours left): expired
        eligible, reason = main.can_cancel_appointment("1405/08/20", "18:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "expired")

        # 6. Past appointment (yesterday): expired
        eligible, reason = main.can_cancel_appointment("1405/08/19", "18:00", now=ref_now)
        self.assertFalse(eligible)
        self.assertEqual(reason, "expired")

if __name__ == '__main__':
    unittest.main()
