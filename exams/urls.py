from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<book_id>[0-9]+)/(?P<exam_type>[wm])/$', views.exam, name='exam'),
    url(r'^aware/(?P<memory_id>[0-9]+)$', views.aware, name='aware'),
    url(r'^forgot/(?P<memory_id>[0-9]+)$', views.forgot, name='forgot'),
]