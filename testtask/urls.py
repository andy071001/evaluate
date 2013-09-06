from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^login', views.LoginHandler.as_view()),
    url(r'^index', views.IndexHandler.as_view()),
    url(r'^upload', views.UploadHandler.as_view()),
    url(r'^get_query_task', views.GetQueryTaskHandler.as_view()),
    #url(r'get_query_word/(?P<page>\d+)/(?P<task_id>\d+)/(?P<query_word_seq>\d+)', views.GetQueryWordHandler.as_view(), name="query_word"),
    url(r'get_query_word', views.GetQueryWordHandler.as_view()),
    url(r'set_bad_reason', views.SetBadReasonHandler.as_view()),
    url(r'^delete_task', views.DeleteTaskHandler.as_view()),
    url(r'^add_word_note', views.AddWordNoteHandler.as_view()),
    url(r'^output_to_excel', views.OutputToExcelHandler.as_view()),
    url(r'^copy_task', views.CopyTaskHandler.as_view()),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/testtask/login'}),
)
