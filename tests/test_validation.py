import unittest
from unittest.mock import patch
import io
import os
import jdatetime
from PIL import Image

import config
import app
import database


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.app = app.app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def _create_dummy_image(self, fmt="JPEG", size=(64, 64), color="green"):
        buf = io.BytesIO()
        img = Image.new("RGB", size, color=color)
        img.save(buf, format=fmt)
        buf.seek(0)
        return buf

    def test_normalize_digits(self):
        """
        Verify Persian and Arabic numerals are accurately normalized to ASCII digits,
        and non-digit/None values are handled safely.
        """
        # Persian numerals
        self.assertEqual(config.normalize_digits("۰۱۲۳۴۵۶۷۸۹"), "0123456789")
        # Arabic numerals
        self.assertEqual(config.normalize_digits("٠١٢٣٤٥٦٧٨٩"), "0123456789")
        # Mixed numerals and text
        self.assertEqual(
            config.normalize_digits("تاریخ: ۱۴۰۵/۰۱/۱۵ ساعت ۱۶:۰۰"),
            "تاریخ: 1405/01/15 ساعت 16:00"
        )
        # Iranian phone in Persian and Arabic digits
        self.assertEqual(config.normalize_digits("۰۹۱۲۳۴۵۶۷۸۹"), "09123456789")
        self.assertEqual(config.normalize_digits("٠٩١٢٣٤٥٦٧٨٩"), "09123456789")
        # ASCII remains unchanged
        self.assertEqual(config.normalize_digits("09123456789"), "09123456789")
        # Safe handling of None and empty string
        self.assertEqual(config.normalize_digits(None), "")
        self.assertEqual(config.normalize_digits(""), "")

    def test_validate_booking_request_regular_user_today_tomorrow(self):
        """
        Regular users booking for today or tomorrow must be rejected with 'advance_notice_required'.
        Booking for 2+ days in advance on a working day must succeed.
        """
        # 1405/08/23 is Saturday (weekday 0)
        ref_now = jdatetime.date(1405, 8, 23)

        # Today: Saturday 1405/08/23
        valid, reason = config.validate_booking_request(
            date_str="1405/08/23",
            time_str="16:00",
            full_name="علی رضایی",
            phone="09123456789",
            is_admin=False,
            now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "advance_notice_required")

        # Tomorrow: Sunday 1405/08/24
        valid, reason = config.validate_booking_request(
            date_str="1405/08/24",
            time_str="16:00",
            full_name="علی رضایی",
            phone="09123456789",
            is_admin=False,
            now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "advance_notice_required")

        # Day after tomorrow: Monday 1405/08/25 (valid working day, >= 2 days advance)
        valid, reason = config.validate_booking_request(
            date_str="1405/08/25",
            time_str="16:00",
            full_name="علی رضایی",
            phone="09123456789",
            is_admin=False,
            now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

    def test_validate_booking_request_admin_today_tomorrow(self):
        """
        Admins can book appointments for today and tomorrow, but cannot book past dates.
        """
        ref_now = jdatetime.date(1405, 8, 23)

        # Admin booking today: Allowed
        valid, reason = config.validate_booking_request(
            date_str="1405/08/23",
            time_str="16:00",
            full_name="دکتر شفائی",
            phone="09123456789",
            is_admin=True,
            now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Admin booking tomorrow: Allowed
        valid, reason = config.validate_booking_request(
            date_str="1405/08/24",
            time_str="16:00",
            full_name="دکتر شفائی",
            phone="09123456789",
            is_admin=True,
            now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Admin booking past date: Rejected
        valid, reason = config.validate_booking_request(
            date_str="1405/08/20",
            time_str="16:00",
            full_name="دکتر شفائی",
            phone="09123456789",
            is_admin=True,
            now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "past_date")

    def test_validate_booking_request_phone_formats(self):
        """
        Accepts valid Iranian mobile numbers (ASCII, Persian, Arabic numerals).
        Rejects short, long, non-Iranian, or malformed numbers.
        """
        ref_now = jdatetime.date(1405, 8, 23)
        valid_date = "1405/08/25"

        # Valid ASCII Iranian mobile
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "09123456789", is_admin=False, now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Valid Persian numerals
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "۰۹۱۲۳۴۵۶۷۸۹", is_admin=False, now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Valid Arabic numerals
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "٠٩١٢٣٤٥٦٧٨٩", is_admin=False, now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Optional/empty phone when None or empty string
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "", is_admin=False, now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Invalid: Too short
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "0912345", is_admin=False, now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "invalid_phone")

        # Invalid: Non-Iranian prefix
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "08123456789", is_admin=False, now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "invalid_phone")

        # Invalid: Malformed / text
        valid, reason = config.validate_booking_request(
            valid_date, "16:00", "سارا احمدی", "invalid_phone", is_admin=False, now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "invalid_phone")

    def test_validate_booking_request_working_hours_and_days(self):
        """
        Validates hours must be in WORKING_HOURS (16:00-20:00).
        Validates days must be in WORKING_WEEKDAYS (Saturday-Wednesday).
        """
        ref_now = jdatetime.date(1405, 8, 23)
        valid_date = "1405/08/25"  # Monday (weekday 2)

        # Valid working hours
        for hr in ["16:00", "17:00", "18:00", "19:00", "20:00"]:
            valid, reason = config.validate_booking_request(
                valid_date, hr, "مریم حسینی", "09123456789", is_admin=False, now=ref_now
            )
            self.assertTrue(valid, f"Expected {hr} to be valid working hour")
            self.assertEqual(reason, "ok")

        # Valid Persian numeral hour
        valid, reason = config.validate_booking_request(
            valid_date, "۱۷:۰۰", "مریم حسینی", "09123456789", is_admin=False, now=ref_now
        )
        self.assertTrue(valid)
        self.assertEqual(reason, "ok")

        # Invalid working hours
        for bad_hr in ["12:00", "21:00", "15:00", "10:30", "invalid"]:
            valid, reason = config.validate_booking_request(
                valid_date, bad_hr, "مریم حسینی", "09123456789", is_admin=False, now=ref_now
            )
            self.assertFalse(valid, f"Expected {bad_hr} to be rejected")
            self.assertEqual(reason, "invalid_time")

        # Non-working days: Thursday (1405/08/28) and Friday (1405/08/29)
        thursday = "1405/08/28"
        valid, reason = config.validate_booking_request(
            thursday, "16:00", "مریم حسینی", "09123456789", is_admin=False, now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "non_working_day")

        friday = "1405/08/29"
        valid, reason = config.validate_booking_request(
            friday, "16:00", "مریم حسینی", "09123456789", is_admin=False, now=ref_now
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "non_working_day")

    def test_app_booking_endpoint_uses_unified_validation(self):
        """
        Test Flask client posting invalid phone or today's date receives flash error and HTTP 400.
        """
        dummy_img = self._create_dummy_image()
        upcoming_valid_days = config.get_upcoming_working_days(1, is_admin=False)
        valid_date = upcoming_valid_days[0]

        # 1. Posting invalid phone format
        response = self.client.post(
            '/booking',
            data={
                'date': valid_date,
                'time': '16:00',
                'full_name': 'رضا علوی',
                'phone': '12345',  # Invalid phone
                'session_type': 'حضوری',
                'receipt': (dummy_img, 'receipt.jpg')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            "موبایل" in response.data.decode('utf-8') or "شماره" in response.data.decode('utf-8'),
            f"Expected phone error in flash response, got: {response.data.decode('utf-8')}"
        )

        # 2. Posting today's date (forbidden for regular users)
        today_str = jdatetime.date.today().strftime("%Y/%m/%d")
        dummy_img2 = self._create_dummy_image()
        response_today = self.client.post(
            '/booking',
            data={
                'date': today_str,
                'time': '16:00',
                'full_name': 'رضا علوی',
                'phone': '09123456789',
                'session_type': 'حضوری',
                'receipt': (dummy_img2, 'receipt.jpg')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(response_today.status_code, 400)
        self.assertTrue(
            "امروز" in response_today.data.decode('utf-8') or "روز" in response_today.data.decode('utf-8'),
            f"Expected advance notice error in flash response, got: {response_today.data.decode('utf-8')}"
        )


if __name__ == '__main__':
    unittest.main()
