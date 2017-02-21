from django.core.management import BaseCommand

from exams import utils
from exams.models import Memory


class Command(BaseCommand):
    help = 'unlock_dt를 새벽 4시로 변경한다.'

    def handle(self, *args, **options):
        memories = Memory.objects.all()
        for memory in memories:
            memory.unlock_dt = utils.normalize_date(memory.unlock_dt)
            memory.save()
