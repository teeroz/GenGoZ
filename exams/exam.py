from datetime import timedelta
from operator import attrgetter
from typing import List

from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from exams.models import Book, Memory, Study, Word, ExamTypes, MemoryStatus


class Exam:
    user = None                 # type: User
    book = None                 # type: Book
    type = ExamTypes.Unknown    # type: ExamTypes

    def __init__(self, exam_type: ExamTypes, user: User = None, book: Book = None, book_id: int = 0):
        self.type = exam_type

        self.user = user

        if book:
            self.book = book
        else:
            self.book = get_object_or_404(Book, pk=book_id)

    @staticmethod
    def get_after_days_by_step(next_step: int) -> int:
        week_days = 7
        month_weeks = 4
        quarter_months = 3
        year_days = 365

        if next_step == 1:
            return 1
        elif next_step == 2:
            return week_days
        elif next_step == 3:
            return week_days * month_weeks
        elif next_step == 4:
            return week_days * month_weeks * quarter_months
        elif next_step >= 5:
            return year_days

    def count_unlocked_words(self) -> int:
        return Memory.objects.filter(user=self.user, book=self.book, type=self.type, unlock_dt__lte=timezone.now())\
                             .count()

    def unlocked_memories(self) -> List[Memory]:
        return Memory.objects.select_related('word') \
                             .filter(user=self.user, book=self.book, type=self.type, unlock_dt__lte=timezone.now())\
                             .order_by('?')

    def add_random_memories(self, number=10) -> None:
        number_of_candidate = 50

        # 일단 많이 틀리지 않았던 단어들도 골고루 나올 수 있게 충분히 많은 수를 추출한 다음에
        recent_studied_unlock_dt = timezone.now() + timedelta(
            days=self.get_after_days_by_step(5) - self.get_after_days_by_step(3))
        random_memories = Memory.objects.select_related('word') \
                                .filter(user=self.user, book=self.book, type=self.type, step=Memory.LastStep,
                                        unlock_dt__lte=recent_studied_unlock_dt) \
                                .order_by('?')[:number_of_candidate]

        # 그 중에서 forgot_cnt가 큰 number개의 단어만 추출한다
        random_memories = sorted(random_memories, key=attrgetter('forgot_cnt'), reverse=True)[:number]

        # 그 단어들을 unlock 시킨다
        for memory in random_memories:
            memory.unlock_dt = timezone.now()
            memory.save()

    def new_or_wrong_words(self) -> List[Memory]:
        return Memory.objects.select_related('word')\
                             .filter(user=self.user, book=self.book, type=self.type, unlock_dt__lte=timezone.now())\
                             .exclude(status=MemoryStatus.Aware)\
                             .order_by('word__id')

    def __queryset_words_to_add(self):
        memory_word_id_list = self.book.memory_set.filter(user=self.user, type=self.type).values_list('word__id')
        words_to_add = self.book.word_set.exclude(id__in=memory_word_id_list)
        if self.type == ExamTypes.Meaning:
            words_to_add = words_to_add.exclude(skip_meaning=True)

        return words_to_add

    def sync_memories(self, count: int = 0):
        words_to_add = self.__queryset_words_to_add()
        if count > 0:
            words_to_add = words_to_add.order_by('id')[:count]
        elif count < 0:
            words_to_add = words_to_add.order_by('-id')[:count*-1]

        for word in words_to_add:   # type: Word
            assert isinstance(word, Word)
            memory = Memory()
            memory.user = self.user
            memory.book = self.book
            memory.word = word
            memory.type = self.type
            memory.unlock_dt = timezone.now()
            memory.save()

    def count_new_words(self):
        return self.__queryset_words_to_add().count()

    def get_random_memory(self) -> Word:
        while True:
            # return Memory.objects.get(pk=1540)
            study_words = Study.objects.select_related('memory', 'word')\
                .filter(user=self.user, word__book=self.book, type=self.type).order_by('id')[:1]
            if len(study_words) <= 0:
                return None
            study_word = study_words[0]    # type: Memory

            if study_word.book_id != study_word.word.book_id:
                study_word.book = study_word.word.book
                study_word.save()

            if self.type == ExamTypes.Meaning and study_word.word.skip_meaning:
                study_word.memory.delete()
                continue

            return study_word

    def count_study_words(self) -> int:
        return Study.objects.filter(user=self.user, word__book=self.book, type=self.type).count()

    def generate_study(self):
        memories = self.unlocked_memories()

        for memory in memories:
            assert isinstance(memory, Memory)

            if memory.book != memory.word.book:
                memory.book = memory.word.book
                memory.save()

            study = Study()
            study.user = self.user
            study.book = self.book
            study.type = self.type
            study.word = memory.word
            study.memory = memory
            study.save()

    def __count_group_by_step(self):
        count_by_step = self.book.memory_set.filter(user=self.user, type=self.type)\
            .values('step').annotate(total=Count('step')).order_by('step')
        retval = {}
        for row in count_by_step:
            retval[row['step']] = row['total']
        return retval

    def get_study_score(self):
        count_by_step = self.__count_group_by_step()
        score = 0
        for step, total in count_by_step.items():
            score += (step * total) / 5.

        return score
