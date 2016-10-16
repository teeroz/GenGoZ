"""GenGoZ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import login, password_change, logout, password_change_done

urlpatterns = [
    url(r'^exams/', include('exams.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^login$', login, {'template_name': 'admin/login.html'}, name='login'),
    url(r'^logout$', logout, {'next_page': '/exams/1/w'}, name='logout'),
    url(r'^password_change$', password_change, {'template_name': 'registration/password_change_form.html'}, name='password_change'),
    url(r'^password_change_done$', password_change_done, {'template_name': 'registration/password_change_done.html'}, name='password_change_done'),
]
