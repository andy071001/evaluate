from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^login', views.LoginHandler.as_view()),
    url(r'^index', views.IndexHandler.as_view()),
    url(r'^upload', views.UploadHandler.as_view()),
)
