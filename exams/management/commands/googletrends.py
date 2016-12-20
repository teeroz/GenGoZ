import re

from django.core.management import BaseCommand

from exams.google import search_num
from exams.models import Word


class Command(BaseCommand):
    help = '단어 테이블에서 한 단어를 가져와 구글 트렌드 수치를 업데이트한다'

    @staticmethod
    def __get_key(word: str):
        key = re.sub(r'(\(.*\))', r'', word)
        key = re.sub(r'([^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+)', r'', key)
        return key

    def handle(self, *args, **options):
        try:
            word = Word.objects.filter(trends__isnull=True)[0]
        except IndexError:
            return

        key = self.__get_key(word.word)
        trends = search_num(key)
        word.trends = trends
        word.save()

        print(word.word + ' : ' + key + ' : ' + str(trends))
