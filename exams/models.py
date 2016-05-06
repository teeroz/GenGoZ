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
    book = models.ForeignKey(Book, on_delete=models.CASCADE, default=1)
    word = models.CharField(max_length=256)
    pronunciation = models.CharField(max_length=256)
    meaning = models.CharField(max_length=256)
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'word')

    def __str__(self):
        return self.book.title + ':' + self.word


MEMORY_TYPES = (
    ('w', 'Word to Meaning and Pronunciation'),
    ('m', 'Meaning to Word and Pronunciation')
)


class Memory(models.Model):
    user = models.ForeignKey(User)
    word = models.ForeignKey(Word)
    type = models.CharField(max_length=1, choices=MEMORY_TYPES)
    step = models.SmallIntegerField()
    unlock_dt = models.DateTimeField()
    right_cnt = models.SmallIntegerField()
    wrong_cnt = models.SmallIntegerField()
    create_dt = models.DateTimeField(auto_now_add=True)
    modify_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'word', 'type')

    def __str__(self):
        return self.user.name + ':' + self.book.title + ':' + self.word + ':' + self.type
