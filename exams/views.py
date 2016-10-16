from datetime import timedelta

from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from exams.exam import Exam
from exams.models import Memory, MemoryStatus, Statistics, Study, ExamTypes, Word


@login_required
def exam(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    study = a_exam.get_random_memory()
    if study is None:
        return start(request, a_exam)

    count_test_words = a_exam.count_study_words()

    word = study.word   # type: Word

    if exam_type == ExamTypes.Word:
        question = study.word.word     # type: str
        question_ex = word.example_jp  # type: str
        answer = study.word.meaning    # type: str
        answer_ex = word.example_kr    # type: str
    elif exam_type == ExamTypes.Meaning:
        question = study.word.meaning  # type: str
        question_ex = word.example_kr  # type: str
        answer = study.word.word       # type: str
        answer_ex = word.example_jp  # type: str
    else:
        raise Http404('Invalid Exam-Type.')

    question_ex = question_ex.replace('[', '<code>').replace(']', '</code>')
    answer_ex = answer_ex.replace('[', '<code>').replace(']', '</code>')

    context = {
        'study': study,
        'question': question,
        'question_ex': question_ex,
        'answer': answer,
        'answer_ex': answer_ex,
        'remain_count': count_test_words,
    }

    return render(request, 'exam.html', context)


@login_required
def start(request: HttpRequest, a_exam: Exam) -> HttpResponse:
    # a_exam.sync_memories()
    count_new_words = a_exam.count_new_words()
    count_test_words = a_exam.count_unlocked_words()
    if count_test_words <= 0 and count_new_words <= 0:
        return render(request, 'finish.html')

    context = {
        'exam': a_exam,
        'book_id': a_exam.book.id,
        'exam_type': a_exam.type,
        'new_count': count_new_words,
        'remain_count': count_test_words,
    }

    return render(request, 'start.html', context)


@login_required
def do_next(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    a_exam.sync_memories(20)
    count_test_words = a_exam.count_unlocked_words()
    if count_test_words <= 0:
        return start(request, a_exam)

    a_exam.generate_study()

    return redirect('exam', book_id=a_exam.book.id, exam_type=a_exam.type)


@login_required
def do_review(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    # a_exam.sync_memories()
    count_test_words = a_exam.count_unlocked_words()
    if count_test_words <= 0:
        return start(request, a_exam)

    a_exam.generate_study()

    return redirect('exam', book_id=a_exam.book.id, exam_type=a_exam.type)


def __get_statistics(memory: Memory) -> Statistics:
    try:
        return Statistics.objects.get(user=memory.user, book=memory.book, exam_date=timezone.now()-timedelta(hours=4),
                                      type=memory.type, step=memory.step, status=memory.status)
    except ObjectDoesNotExist:
        return Statistics(user=memory.user, book=memory.book, exam_date=timezone.now()-timedelta(hours=4),
                          type=memory.type, step=memory.step, status=memory.status)


@login_required
def list_page(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    unlocked_memories = a_exam.unlocked_memories()
    if len(unlocked_memories) <= 0:
        return render(request, 'finish.html')

    context = {
        'exam': a_exam,
        'memories': unlocked_memories
    }

    return render(request, 'list.html', context)


@login_required
def new_words(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    words = a_exam.new_or_wrong_words()

    context = {
        'exam': a_exam,
        'memories': words
    }

    return render(request, 'list.html', context)


@login_required
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
            memory.unlock_dt = timezone.now() + timedelta(days=365)
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


@login_required
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
