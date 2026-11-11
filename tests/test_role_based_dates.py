import unittest
import jdatetime
from main import get_upcoming_days

class TestRoleBasedDates(unittest.TestCase):
    def test_admin_gets_today_and_tomorrow(self):
        # 1405/08/23 is Saturday (weekday 0)
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, is_admin=True, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertEqual(len(days), 5)
        self.assertEqual(dates[0], "1405/08/23")
        self.assertEqual(dates[1], "1405/08/24")
        self.assertEqual(days[0][1], "شنبه")
        self.assertEqual(days[1][1], "یکشنبه")

    def test_regular_user_skips_today_and_tomorrow(self):
        # 1405/08/23 is Saturday (weekday 0)
        # Saturday + 2 days = Monday (1405/08/25, weekday 2)
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, is_admin=False, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertEqual(len(days), 5)
        self.assertNotIn("1405/08/23", dates)
        self.assertNotIn("1405/08/24", dates)
        self.assertEqual(dates[0], "1405/08/25")
        self.assertEqual(days[0][1], "دوشنبه")

    def test_default_is_admin_is_false(self):
        ref_date = jdatetime.date(1405, 8, 23)
        days = get_upcoming_days(days_count=5, reference_date=ref_date)
        dates = [d[0].strftime("%Y/%m/%d") for d in days]
        
        self.assertNotIn("1405/08/23", dates)
        self.assertNotIn("1405/08/24", dates)

if __name__ == "__main__":
    unittest.main()
