import re

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models


class ExamTypes:
    Word = 'w'
    Meaning = 'm'
    Unknown = ''

EXAM_TYPES = (
    (ExamTypes.Word, 'Word'),
    (ExamTypes.Meaning, 'Meaning'),
)


class Book(models.Model):
    title = models.CharField(max_length=64, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Word(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    word = models.CharField(max_length=256)
    pronunciation = models.CharField(max_length=256, blank=True)
    meaning = models.CharField(max_length=256)
    example_jp = models.CharField(max_length=256, blank=True)
    example_kr = models.CharField(max_length=256, blank=True)
    note = models.CharField(max_length=256, blank=True)
    naver_link = models.CharField(max_length=256, blank=True)
    skip_meaning = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)
    related = models.ManyToManyField("self", symmetrical=True, blank=True)
    synonym = models.ManyToManyField("self", symmetrical=True, blank=True)
    antonym = models.ManyToManyField("self", symmetrical=True, blank=True)
    trends = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('book', 'word')
        index_together = (
            ('book', 'create_dt'),
        )

    def word_with_link(self):
        return re.sub(r'([\u4e00-\u9fff])', r'<span class="kanzi">\1</span>', self.word)

    def example_with_link(self):
        return re.sub(r'([\u4e00-\u9fff]+)', r'<span class="kanzi">\1</span>', self.example_jp)

    def example_jp_with_tag(self):
        return self.example_jp.replace('[', '<code>').replace(']', '</code>')

    def example_kr_with_tag(self):
        return self.example_kr.replace('[', '<code>').replace(']', '</code>')

    def get_absolute_url(self):
        if self.naver_link:
            return 'http://jpdic.naver.com/entry/jk/%s.nhn' % self.naver_link
        else:
            return 'http://jpdic.naver.com/search.nhn?range=word&page=1&q=%s' % self.word

    def string_with_naver_link(self):
        content = '%s(%s)' % (self.word, self.meaning)
        html = '<a href="%s" target="_blank">%s</a>' % (self.get_absolute_url(), 'View on Naver')
        return html

    def string_with_link(self):
        content = '%s(%s)' % (self.word, self.meaning)
        # html = '<a href="%s" target="_blank">%s</a>' % (self.get_absolute_url(), content)
        html = '<a href="%s">%s</a>' % (reverse('detail', args=[self.id]), content)
        return html

    def related_terms(self) -> str:
        result = []
        related_str = ', '.join([p.word for p in self.related.all()])
        if related_str:
            result.append('[관] %s' % related_str)
        synonym_str = ', '.join([p.word for p in self.synonym.all()])
        if synonym_str:
            result.append('[유] %s' % synonym_str)
        antonym_str = ', '.join([p.word for p in self.antonym.all()])
        if antonym_str:
            result.append('[반] %s' % antonym_str)
        return ' / '.join(result)

    def __str__(self):
        return '%s:%s:%s' % (self.word, self.pronunciation, self.meaning)


class MemoryStatus:
    Unknown = 'u'
    Aware = 'a'
    Forgot = 'f'

MEMORY_STATUS = (
    ('u', 'Unknown'),
    ('a', 'Aware'),
    ('f', 'Forgot'),
)


class Memory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)    # type: User
    book = models.ForeignKey(Book, on_delete=models.CASCADE)    # type: Book
    word = models.ForeignKey(Word, on_delete=models.CASCADE)    # type: Word
    type = models.CharField(max_length=1, choices=EXAM_TYPES)
    step = models.SmallIntegerField(default=0)
    unlock_dt = models.DateTimeField()
    status = models.CharField(max_length=1, choices=MEMORY_STATUS, default=MemoryStatus.Unknown)
    group_level = models.SmallIntegerField(default=0)
    aware_cnt = models.SmallIntegerField(default=0)
    forgot_cnt = models.SmallIntegerField(default=0)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'word', 'type')
        index_together = (
            ('user', 'book', 'type', 'create_dt'),
            ('user', 'book', 'type', 'unlock_dt')
        )

    def __str__(self):
        return self.user.username + ':' + self.book.title + ':' + self.word.word + ':' + self.type

    def question(self) -> str:
        if self.type == ExamTypes.Meaning:
            return self.word.meaning
        elif self.type == ExamTypes.Word:
            return self.word.word

    def answer(self) -> str:
        if self.type == ExamTypes.Meaning:
            return self.word.word
        elif self.type == ExamTypes.Word:
            return self.word.meaning


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    exam_date = models.DateField()
    type = models.CharField(max_length=1, choices=EXAM_TYPES)
    step = models.SmallIntegerField()
    status = models.CharField(max_length=1, choices=MEMORY_STATUS)
    aware_cnt = models.IntegerField(default=0)
    forgot_cnt = models.IntegerField(default=0)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book', 'type', 'step', 'status', 'exam_date')


class Study(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)    # type: User
    book = models.ForeignKey(Book, on_delete=models.CASCADE)    # type: Book
    type = models.CharField(max_length=1, choices=EXAM_TYPES)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)    # type: Word
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE)    # type: Memory
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book', 'type', 'word')

    def word_kanzi(self):
        return self.word.word

    def word_pronunciation(self):
        return self.word.pronunciation

    def word_meaning(self):
        return self.word.meaning
