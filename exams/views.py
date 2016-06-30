from datetime import timedelta, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from exams.models import Book, Memory, User, MemoryTypes, Word, MemoryStatus, Statistics, Study


def index(request: HttpRequest) -> HttpResponse:
    print(request)
    return HttpResponse("Hello, world")


def __get_user() -> User:
    return User.objects.get(pk=1)


def __sync_memories(user: User, book: Book, exam_type: str):
    memories = book.memory_set.filter(user=user, type=exam_type).order_by('-create_dt')[:1]

    if len(memories) <= 0:
        words_to_add = book.word_set.filter()
    else:
        words_to_add = book.word_set.filter(create_dt__gt=memories[0].create_dt)

    for word in words_to_add:   # type: Word
        assert isinstance(word, Word)
        memory = Memory()
        memory.user = user
        memory.book = book
        memory.word = word
        memory.type = exam_type
        memory.unlock_dt = timezone.now()
        memory.save()


def __generate_study(user: User, book: Book, exam_type: str):
    memories = Memory.objects.filter(user=user, word__book=book, type=exam_type, unlock_dt__lte=timezone.now())\
                     .order_by('?')

    for memory in memories:
        assert isinstance(memory, Memory)

        if memory.book != memory.word.book:
            memory.book = memory.word.book
            memory.save()

        study = Study()
        study.user = user
        study.book = book
        study.word = memory.word
        study.type = exam_type
        study.memory = memory
        study.save()


def __get_random_memory(user: User, book: Book, exam_type: str) -> Word:
    while True:
        # return Memory.objects.get(pk=1540)
        study_words = Study.objects.filter(user=user, word__book=book, type=exam_type)[:1]
        if len(study_words) <= 0:
            return None
        study_word = study_words[0]    # type: Memory

        if study_word.book != study_word.word.book:
            study_word.book = study_word.word.book
            study_word.save()

        return study_word


def __count_study_words(user: User, book: Book, exam_type: str) -> int:
    return Study.objects.filter(user=user, word__book=book, type=exam_type).count()


def exam(request: HttpRequest, book_id: int, exam_type: str) -> HttpResponse:
    user = __get_user()
    book = get_object_or_404(Book, pk=book_id)  # type: Book

    study = __get_random_memory(user, book, exam_type)
    if study is None:
        return start(request, user, book, exam_type)

    count_test_words = __count_study_words(user, book, exam_type)

    if exam_type == MemoryTypes.Word:
        question = study.word.word     # type: str
        answer = study.word.meaning    # type: str
    elif exam_type == MemoryTypes.Meaning:
        question = study.word.meaning  # type: str
        answer = study.word.word    # type: str
    else:
        raise Http404('Invalid Exam-Type.')

    context = {
        'study': study,
        'question': question,
        'answer': answer,
        'remain_count': count_test_words,
    }

    return render(request, 'exam.html', context)


def __count_unlocked_words(user: User, book: Book, exam_type: str) -> int:
    return Memory.objects.filter(user=user, book=book, type=exam_type, unlock_dt__lte=timezone.now()).count()


def start(request: HttpRequest, user: User, book: Book, exam_type: str) -> HttpResponse:
    __sync_memories(user, book, exam_type)
    count_test_words = __count_unlocked_words(user, book, exam_type)
    if count_test_words <= 0:
        return render(request, 'finish.html')

    context = {
        'book_id': book.id,
        'exam_type': exam_type,
        'remain_count': count_test_words,
    }

    return render(request, 'start.html', context)


def do_start(request: HttpRequest, book_id: str, exam_type: str) -> HttpResponse:
    user = __get_user()
    book = get_object_or_404(Book, pk=book_id)  # type: Book

    __sync_memories(user, book, exam_type)
    count_test_words = __count_unlocked_words(user, book, exam_type)
    if count_test_words <= 0:
        return render(request, 'finish.html')

    __generate_study(user, book, exam_type)

    return redirect('exam', book_id=book.id, exam_type=exam_type)


def __get_statistics(memory: Memory) -> Statistics:
    try:
        return Statistics.objects.get(user=memory.user, book=memory.book, exam_date=timezone.now()-timedelta(hours=4),
                                      type=memory.type, step=memory.step, status=memory.status)
    except ObjectDoesNotExist:
        return Statistics(user=memory.user, book=memory.book, exam_date=timezone.now()-timedelta(hours=4),
                          type=memory.type, step=memory.step, status=memory.status)


def aware(request: HttpRequest, study_id: int) -> HttpResponse:
    study = get_object_or_404(Study, pk=study_id)    # type: Memory
    memory = study.memory

    # 첫 테스트에 바로 맞췄다면
    if memory.group_level <= 0:
        # 통계 업데이트
        statistics = __get_statistics(memory)
        statistics.aware_cnt += 1
        statistics.save()

        # step을 증가시키고, 그에 맞게 unlock_dt 시각을 변경한다
        if memory.step == 0:
            memory.unlock_dt = timezone.now() + timedelta(days=1)
        elif memory.step == 1:
            memory.unlock_dt = timezone.now() + timedelta(days=7)
        elif memory.step == 2:
            memory.unlock_dt = timezone.now() + timedelta(days=28)
        elif memory.step == 3:
            memory.unlock_dt = timezone.now() + timedelta(days=28*3)
        elif memory.step == 4:
            memory.unlock_dt = datetime.max()
        memory.unlock_dt = memory.unlock_dt - timedelta(hours=8)
        memory.step += 1

        # 한번에 맞췄다면 이 단어는 안다고 볼 수 있다
        memory.status = MemoryStatus.Aware

        # 한번에 맞췄다는 숫자 표시
        memory.aware_cnt += 1
    # 두번째 이후에 맞췄다면
    else:
        # 내일 다시 테스트한다
        memory.unlock_dt = timezone.now() + timedelta(hours=16)

        # 한번이라도 틀리면 스텝0부터 다시 시작한다
        memory.step = 0

    memory.group_level = 0
    memory.save()

    study.delete()

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)


def forgot(request: HttpRequest, study_id: int) -> HttpResponse:
    study = get_object_or_404(Study, pk=study_id)    # type: Study
    memory = study.memory

    # 첫 테스트라면
    if memory.group_level <= 0:
        # 통계 업데이트
        statistics = __get_statistics(memory)
        statistics.forgot_cnt += 1
        statistics.save()

        # 한번에 못 맞췄다는 숫자 표시
        memory.forgot_cnt += 1

    memory.status = MemoryStatus.Forgot
    memory.group_level += 1
    memory.save()

    study.delete()

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)
