from datetime import timedelta, datetime


def normalize_date(a_datetime: datetime) -> datetime:
    """
    a_datetime을 4시간 이전 날짜의 새벽 4시 시각으로 변경한다.
    복습으로 다시 나오는 시각을 다음날 새벽 4시로 고정하기 위하여 사용한다.
    자정부터 새벽 4시까지 학습한 경우에는 잠들기 전에 학습한 것으로 간주하여 그 날 새벽 4시에 나오도록 한다.
    :param a_datetime:
    :return:
    """
    result = a_datetime.astimezone(tz=None)
    result = result - timedelta(hours=4)
    result = datetime(result.year, result.month, result.day, 4, tzinfo=result.tzinfo)
    return result
