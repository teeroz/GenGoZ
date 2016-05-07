from datetime import timedelta, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from exams.models import Book, Memory, User, MemoryTypes, Word, MemoryStatus, Statistics


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
        memory.word = word
        memory.book = book
        memory.type = exam_type
        memory.save()


def __get_random_memory(user: User, book: Book, exam_type: str) -> Word:
    # return Memory.objects.get(pk=819)
    memories = Memory.objects.filter(user=user, book=book, type=exam_type, unlock_dt__lte=timezone.now()) \
                     .order_by('group_level', '?')[:1]
    if len(memories) <= 0:
        return None
    else:
        return memories[0]


def __get_remain_count(user: User, book: Book, exam_type: str) -> int:
    return Memory.objects.filter(user=user, book=book, type=exam_type, unlock_dt__lte=timezone.now()).count()


def exam(request: HttpRequest, book_id: int, exam_type: str) -> HttpResponse:
    user = __get_user()
    book = get_object_or_404(Book, pk=book_id)  # type: Book

    __sync_memories(user, book, exam_type)
    memory = __get_random_memory(user, book, exam_type)
    remain_count = __get_remain_count(user, book, exam_type)

    if memory is None:
        return render(request, 'finish.html')

    if exam_type == MemoryTypes.Word:
        question = memory.word.word     # type: str
        answer = memory.word.meaning    # type: str
    elif exam_type == MemoryTypes.Meaning:
        question = memory.word.meaning  # type: str
        answer = memory.word.word    # type: str
    else:
        raise Http404('Invalid Exam-Type.')

    context = {
        'memory': memory,
        'question': question,
        'answer': answer,
        'remain_count': remain_count,
    }

    return render(request, 'exam.html', context)


def __get_statistics(memory: Memory) -> Statistics:
    try:
        return Statistics.objects.get(user=memory.user, book=memory.book, exam_date=timezone.now(),
                                      type=memory.type, step=memory.step, status=memory.status)
    except ObjectDoesNotExist:
        return Statistics(user=memory.user, book=memory.book, exam_date=timezone.now(),
                          type=memory.type, step=memory.step, status=memory.status)


def aware(request: HttpRequest, memory_id: int) -> HttpResponse:
    memory = get_object_or_404(Memory, pk=memory_id)    # type: Memory

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

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)


def forgot(request: HttpRequest, memory_id: int) -> HttpResponse:
    memory = get_object_or_404(Memory, pk=memory_id)    # type: Memory

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

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)
