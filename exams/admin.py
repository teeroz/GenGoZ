from datetime import datetime

from django.contrib import admin
from django.contrib.auth import get_user
from django.forms import ModelForm
from django.utils import timezone

from exams.models import Book, Word, Memory, Statistics, Study


def local_time(value: datetime):
    return timezone.localtime(value)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title', 'create_dt')
    list_display_links = ('title',)
    ordering = ['-create_dt']
    list_select_related = ('owner',)


class WordModelForm(ModelForm):
    class Meta:
        model = Word
        exclude = ('create_dt', 'modify_dt')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance:
            book = instance.book
        else:
            if self.current_user.username == 'kaien':
                book = Book.objects.get(pk=6)
            else:
                book = Book.objects.get(pk=1)
            kwargs['initial'] = {'book': book}

        ModelForm.__init__(self, *args, **kwargs)

        queryset = Word.objects.filter(book=book)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        self.fields['related'].queryset = queryset
        self.fields['synonym'].queryset = queryset
        self.fields['antonym'].queryset = queryset


def __copy_word(word: Word, book: Book):
    is_exist = Word.objects.filter(book=book, word=word.word).count() > 0
    if is_exist:
        return

    word.pk = None
    word.book = book
    word.save()


def copy_words(modeladmin, request, queryset):
    kaien_book = Book.objects.get(pk=6)

    for word in queryset:
        __copy_word(word, kaien_book)
copy_words.short_description = 'Copy words to kaien words'


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'word', 'meaning', 'trends', 'related_terms', 'created_at')
    list_display_links = ('word',)
    list_filter = ('book',)
    filter_horizontal = ('related', 'synonym', 'antonym')
    ordering = ['-create_dt']
    preserve_filters = True
    search_fields = ('word', 'pronunciation', 'meaning')
    list_select_related = ('book',)
    save_on_top = True
    form = WordModelForm
    actions = [copy_words]

    def get_form(self, request, obj=None, **kwargs):
        form = super(WordAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    @staticmethod
    def created_at(obj: Memory) -> str:
        return local_time(obj.create_dt).strftime('%m.%d %H:%M')


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'word_title', 'type', 'step', 'unlocked_at', 'status',
                    'group_level', 'aware_cnt', 'forgot_cnt', 'modified_at', 'unlock_dt')
    list_display_links = ('id',)
    list_filter = ('user', 'book', 'type', 'step', 'status')
    ordering = ['-modify_dt']
    preserve_filters = True
    save_on_top = True
    list_select_related = ('user', 'book', 'word')
    search_fields = ('word__word', 'word__pronunciation', 'word__meaning')

    @staticmethod
    def word_title(obj: Memory) -> str:
        return obj.word.word

    @staticmethod
    def unlocked_at(obj: Memory) -> str:
        if obj.unlock_dt < timezone.now():
            return 'UNLOCKED'
        else:
            return local_time(obj.unlock_dt).strftime('%m.%d %H:%M')

    @staticmethod
    def modified_at(obj: Memory) -> str:
        return local_time(obj.modify_dt).strftime('%m.%d %H:%M')


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'exam_date', 'type', 'step', 'status', 'aware_cnt', 'forgot_cnt')
    list_display_links = ('id',)
    list_filter = ('user', 'book', 'type', 'step', 'status')
    ordering = ['user', 'book', '-exam_date', 'type', 'step', 'status']
    preserve_filters = True
    list_select_related = ('user', 'book')

    @staticmethod
    def modified_at(obj: Memory) -> str:
        return local_time(obj.modify_dt).strftime('%m.%d %H:%M')


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'word_kanzi', 'word_pronunciation', 'word_meaning', 'type')
    list_display_links = ('word_kanzi',)
    list_filter = ('book', 'type')
    preserve_filters = True
    save_on_top = True

