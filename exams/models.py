from django.db import models


class User(models.Model):
    name = models.CharField(max_length=32, unique=True)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


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
    naver_link = models.CharField(max_length=256, blank=True)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)
    related = models.ManyToManyField("self", symmetrical=True, blank=True)
    synonym = models.ManyToManyField("self", symmetrical=True, blank=True)
    antonym = models.ManyToManyField("self", symmetrical=True, blank=True)

    class Meta:
        unique_together = ('book', 'word')
        index_together = (
            ('book', 'create_dt'),
        )

    def get_absolute_url(self):
        return 'http://jpdic.naver.com/entry/jk/%s.nhn' % self.naver_link

    def string_with_link(self):
        content = '%s(%s)' % (self.word, self.meaning)
        if self.naver_link:
            html = '<a href="%s" target="_blank">%s</a>' % (self.get_absolute_url(), content)
        else:
            html = content
        return html

    def __str__(self):
        return '%s:%s:%s' % (self.word, self.pronunciation, self.meaning)


class MemoryTypes:
    Word = 'w'
    Meaning = 'm'

MEMORY_TYPES = (
    ('w', 'Word'),
    ('m', 'Meaning'),
)


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=MEMORY_TYPES)
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
        return self.user.name + ':' + self.book.title + ':' + self.word.word + ':' + self.type


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    exam_date = models.DateField()
    type = models.CharField(max_length=1, choices=MEMORY_TYPES)
    step = models.SmallIntegerField()
    status = models.CharField(max_length=1, choices=MEMORY_STATUS)
    aware_cnt = models.IntegerField(default=0)
    forgot_cnt = models.IntegerField(default=0)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book', 'type', 'step', 'status', 'exam_date')
