from django.contrib import admin

from exams.models import Book, Word, Memory, User


@admin.register(User)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'create_dt')
    list_display_links = ('name', )
    ordering = ['-create_dt']


@admin.register(Book)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'create_dt')
    list_display_links = ('title', )
    ordering = ['-create_dt']


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'word', 'pronunciation', 'meaning', 'create_dt')
    list_display_links = ('word', )
    list_filter = ('book', )
    ordering = ['-create_dt']
    preserve_filters = True
    search_fields = ('word', 'pronunciation', 'meaning')

admin.site.register(Memory)
