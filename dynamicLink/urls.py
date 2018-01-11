# -*- coding:utf-8 -*-
# This Python file uses the following encoding: utf-8

from django.conf.urls import url, include
from dynamicLink.views import site, fetch

urlpatterns = [
                       url(r'^site/([\w-]*)/$', site, name='site'),
                       url(r'^link/(\w{1,100})/.*$', fetch, name='fetch'),
                       url(r'^link/(\w{1,100})$', fetch, name='fetch'), # without prefix
]

