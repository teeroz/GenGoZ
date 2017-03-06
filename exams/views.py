from datetime import timedelta

from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest, Http404
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from exams import utils
from exams.exam import Exam
from exams.models import Memory, MemoryStatus, Statistics, Study, ExamTypes, Word, Book


@login_required
def exam(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    study = a_exam.get_random_memory()
    if study is None:
        return start(request, a_exam)

    count_test_words = a_exam.count_study_words()

    word = study.word   # type: Word

    if word.word == word.pronunciation:
        word.pronunciation = ''
        word.save()

    if exam_type == ExamTypes.Word:
        question = study.word.word_with_link()  # type: str
        question_ex = word.example_with_link()  # type: str
        answer = study.word.meaning             # type: str
        answer_ex = word.example_kr             # type: str
        if user.username == 'teeroz':
            can_reset_meaning = True            # type: bool
        else:
            can_reset_meaning = False           # type: bool
    elif exam_type == ExamTypes.Meaning:
        question = study.word.meaning           # type: str
        question_ex = word.example_kr           # type: str
        answer = study.word.word_with_link()    # type: str
        answer_ex = word.example_with_link()    # type: str
        can_reset_meaning = False               # type: bool
    else:
        raise Http404('Invalid Exam-Type.')

    question_ex = question_ex.replace('[', '<code>').replace(']', '</code>')
    answer_ex = answer_ex.replace('[', '<code>').replace(']', '</code>')

    context = {
        'book_id': book_id,
        'study': study,
        'question': question,
        'question_ex': question_ex,
        'answer': answer,
        'answer_ex': answer_ex,
        'remain_count': count_test_words,
        'note': word.note,
        'can_reset_meaning': can_reset_meaning,
    }

    return render(request, 'exam.html', context)


@login_required
def detail_page(request: HttpRequest, word_id: int) -> HttpResponse:
    word = get_object_or_404(Word, pk=word_id)

    context = {
        'word': word,
    }

    return render(request, 'detail.html', context)


@login_required
def start(request: HttpRequest, a_exam: Exam) -> HttpResponse:
    user = get_user(request)
    # a_exam.sync_memories()
    count_new_words = a_exam.count_new_words()
    count_test_words = a_exam.count_unlocked_words()
    """
    if count_test_words <= 0 and count_new_words <= 0:
        return render(request, 'finish.html')
    """
    study_score = a_exam.get_study_score()

    if user.username == 'teeroz':
        include_random_memories = True
    else:
        include_random_memories = False

    context = {
        'exam': a_exam,
        'book_id': a_exam.book.id,
        'exam_type': a_exam.type,
        'new_count': count_new_words,
        'remain_count': count_test_words,
        'study_score': int(study_score),
        'include_random_memories': include_random_memories,
    }

    return render(request, 'start.html', context)


@login_required
def do_add_random(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)
    a_exam.add_random_memories()

    return redirect('exam', book_id=a_exam.book.id, exam_type=a_exam.type)


@login_required
def do_next(request: HttpRequest, book_id: int, exam_type: ExamTypes) -> HttpResponse:
    user = get_user(request)
    a_exam = Exam(book_id=book_id, exam_type=exam_type, user=user)

    if user.username == 'kaien' or user.username == 'taek':
        a_exam.sync_memories(-20)
    elif user.username == 'teeroz':
        a_exam.sync_memories()
    else:
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
def search_page(request: HttpRequest, book_id: int) -> HttpResponse:
    book = get_object_or_404(Book, pk=book_id)
    keyword = request.GET['k']
    words = book.word_set.filter(word__contains=keyword).order_by('pronunciation')

    context = {
        'words': words
    }

    return render(request, 'search.html', context)


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
    study = get_object_or_404(Study, pk=study_id)  # type: Memory
    memory = study.memory
    statistics = __get_statistics(memory)

    # 첫 테스트에 바로 맞췄다면
    if memory.group_level <= 0:
        # 통계 업데이트
        statistics.aware_cnt += 1

        # 한번에 맞췄다는 숫자 표시
        memory.aware_cnt += 1

        # step을 증가시키고, 그에 맞게 unlock_dt 시각을 변경한다
        if memory.step <= 4:
            memory.step += 1
        else:  # memory.step >= 5
            if memory.forgot_cnt > 0:
                memory.forgot_cnt -= 1

        # 한번에 맞췄다면 이 단어는 안다고 볼 수 있다
        memory.status = MemoryStatus.Aware

    # 두번째 이후에 맞췄다면
    else:
        # 통계 업데이트
        statistics.forgot_cnt += 1

        # 한번에 못 맞췄다는 숫자 표시
        memory.forgot_cnt += 1

        # 한번이라도 틀리면 스텝1부터 다시 시작한다
        memory.step = 1

        # 한번에 못맞췄다면 이 단어는 모른다고 볼 수 있다
        memory.status = MemoryStatus.Forgot

    memory.unlock_dt = timezone.now() + timedelta(days=Exam.get_after_days_by_step(memory.step))
    memory.unlock_dt = utils.normalize_date(memory.unlock_dt)

    memory.group_level = 0

    statistics.save()
    memory.save()
    study.delete()

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)


@login_required
def forgot(request: HttpRequest, study_id: int) -> HttpResponse:
    study = get_object_or_404(Study, pk=study_id)  # type: Study
    memory = study.memory

    memory.group_level += 1
    memory.save()

    study.delete()

    return redirect('exam', book_id=memory.book.id, exam_type=memory.type)


@login_required
def reset_meaning(request: HttpRequest, study_id: int) -> JsonResponse:
    user = get_user(request)
    study = get_object_or_404(Study, pk=study_id)    # type: Study
    try:
        memory = Memory.objects.get(user=user, word=study.word, type=ExamTypes.Meaning)
    except ObjectDoesNotExist:
        return JsonResponse({'result': True})

    memory.change_to_initial_step()

    return JsonResponse({'result': True})
