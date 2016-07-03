from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<book_id>[0-9]+)/(?P<exam_type>[wm])$', views.exam, name='exam'),
    url(r'^aware/(?P<study_id>[0-9]+)$', views.aware, name='aware'),
    url(r'^forgot/(?P<study_id>[0-9]+)$', views.forgot, name='forgot'),
    url(r'^do_start/(?P<book_id>[0-9]+)/(?P<exam_type>[wm])$', views.do_start, name='do_start'),
    url(r'^list/(?P<book_id>[0-9]+)/(?P<exam_type>[wm])$', views.list_page, name='list'),
    url(r'^new_words/(?P<book_id>[0-9]+)/(?P<exam_type>[wm])$', views.new_words, name='new_words'),
]
