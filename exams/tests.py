from datetime import datetime, timezone

from django.test import TestCase

from exams import utils


class ExamsTestCase(TestCase):
    def setUp(self):
        pass

    def test_normalize_date(self):
        tz_local = datetime.now(timezone.utc).astimezone(tz=None).tzinfo

        a_datetime = datetime.strptime('2017-02-21 03:39:53.438223+0000', '%Y-%m-%d %H:%M:%S.%f%z')
        result = utils.normalize_date(a_datetime)
        expected = datetime(2017, 2, 21, 4, tzinfo=tz_local)
        self.assertEqual(result, expected)

        a_datetime = datetime.strptime('2017-02-20 02:00:00.000000+0900', '%Y-%m-%d %H:%M:%S.%f%z')
        result = utils.normalize_date(a_datetime)
        expected = datetime(2017, 2, 19, 4, tzinfo=tz_local)
        self.assertEqual(result, expected)

        a_datetime = datetime.strptime('2017-02-20 05:00:00.000000+0900', '%Y-%m-%d %H:%M:%S.%f%z')
        result = utils.normalize_date(a_datetime)
        expected = datetime(2017, 2, 20, 4, tzinfo=tz_local)
        self.assertEqual(result, expected)

        a_datetime = datetime.strptime('2017-02-20 00:00:00.000000+0900', '%Y-%m-%d %H:%M:%S.%f%z')
        result = utils.normalize_date(a_datetime)
        expected = datetime(2017, 2, 19, 4, tzinfo=tz_local)
        self.assertEqual(result, expected)

        a_datetime = datetime.strptime('2017-02-20 04:00:00.000000+0900', '%Y-%m-%d %H:%M:%S.%f%z')
        result = utils.normalize_date(a_datetime)
        expected = datetime(2017, 2, 20, 4, tzinfo=tz_local)
        self.assertEqual(result, expected)

