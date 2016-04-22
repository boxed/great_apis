"""foo URL Configuration

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
from django.conf.urls import url
from django.contrib import admin

from foo.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^triadmin/(?P<app_name>\w+)?/?(?P<model_name>\w+)?/?(?P<pk>\d+)?/?(?P<command>\w+)?/?', triadmin_impl),

    url(r'^1/$', example1),
    url(r'^2/$', example2),
    url(r'^3/$', example3),
    url(r'^4/$', example4),
    url(r'^5/$', example5),
    # url(r'^create/$', create),
    # url(r'^(?P<pk>\d+)/edit/$', edit),
]
