from typing import List

from django.shortcuts import get_object_or_404
from django.utils import timezone

from exams.models import Book, Memory, Study, User, Word, ExamTypes


class Exam:
    user = None                 # type: User
    book = None                 # type: Book
    type = ExamTypes.Unknown    # type: ExamTypes

    def __init__(self, exam_type: ExamTypes, user: User = None, book: Book = None, book_id: int = 0):
        self.type = exam_type

        if user:
            self.user = user
        else:
            self.user = User.objects.get(pk=1)

        if book:
            self.book = book
        else:
            self.book = get_object_or_404(Book, pk=book_id)

    def count_unlocked_words(self) -> int:
        return Memory.objects.filter(user=self.user, book=self.book, type=self.type, unlock_dt__lte=timezone.now())\
                             .count()

    def unlocked_memories(self) -> List[Memory]:
        return Memory.objects.select_related('word')\
                             .filter(user=self.user, book=self.book, type=self.type, unlock_dt__lte=timezone.now())\
                             .order_by('?')

    def sync_memories(self):
        memories = self.book.memory_set.filter(user=self.user, type=self.type).order_by('-create_dt')[:1]

        if len(memories) <= 0:
            words_to_add = self.book.word_set.filter()
        else:
            words_to_add = self.book.word_set.filter(create_dt__gt=memories[0].create_dt)

        for word in words_to_add:   # type: Word
            assert isinstance(word, Word)
            memory = Memory()
            memory.user = self.user
            memory.book = self.book
            memory.word = word
            memory.type = self.type
            memory.unlock_dt = timezone.now()
            memory.save()

    def get_random_memory(self) -> Word:
        while True:
            # return Memory.objects.get(pk=1540)
            study_words = Study.objects.filter(user=self.user, word__book=self.book, type=self.type)[:1]
            if len(study_words) <= 0:
                return None
            study_word = study_words[0]    # type: Memory

            if study_word.book != study_word.word.book:
                study_word.book = study_word.word.book
                study_word.save()

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
