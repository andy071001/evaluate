#coding=utf8
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic import ListView
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login

import random
import urllib
import urllib2
import threading
import Queue
import datetime
from sgmllib import SGMLParser

from .models import Task, QueryWord, QueryItem
from .constants import (
    VERIFY_CODE_LENGTH, 
    CON_REQ, 
    makepolo_url, 
    alibaba_url,
    QUERY_WORD_PER_PAGE,
)


def generate_verify_code():
    a = range(0, 10)
    code = ""
    for i in range(0, VERIFY_CODE_LENGTH):
        code += str(random.choice(a))

    return code


class LoginHandler(View):
    def get(self, request):
        verify_code = generate_verify_code()
        return render_to_response('testtask/login.html', 
            {'verify_code': verify_code},
            context_instance = RequestContext(request))

    def post(self, request):
        username = request.POST['name']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse("Login Successfully!")
            else:
                return HttpResponse("Disabled Account!")
        else:
            return HttpResponse("invalid login")


class IndexHandler(ListView):
    template_name = 'testtask/index.html'
    def get_queryset(self):
        return []


class UploadHandler(View):
    def get(self, request):
        return render_to_response('testtask/upload.html', 
            context_instance = RequestContext(request))

    def post(self, request):
        print "request.user:"
        print request.user
        name = request.POST['name']
        type = int(request.POST['type'])
        file_handler = request.FILES.get('file', None)
        query_text_list = file_handler.readlines()
        process_query(query_text_list, name, type, request.user)
        file_handler.close()
        return HttpResponse("good")


def process_query(query_text_list, name, type, user):
    if (Task.objects.filter(creator=user, name=name, type=type).exists()):
        return HttpResponse("task exists!")
    task = Task.objects.create(
        name=name,
        creator=user,
        create_time=datetime.datetime.now(),
        type=type,
        number = len(query_text_list),
    )

    query_url_list = []
    for item in query_text_list:
        item = item.strip()  # 去除首尾空白
        # makepolo
        query_url = makepolo_url + urllib.quote(item)
        print query_url
        try:
            utf8_item = unicode(item, "gbk").encode("utf8")
        except Exception, e:
            utf8_item = item

        word_item1 = QueryWord.objects.create(
            task=task, 
            source="makepolo", 
            query_text=utf8_item,
        )
        query_url_list.append((query_url, word_item1))
        
        # alibaba
        query_url = alibaba_url + urllib.quote(item)
        print query_url
        word_item2 = QueryWord.objects.create(
            task=task, 
            source="alibaba", 
            query_text=utf8_item,
        )
        query_url_list.append((query_url, word_item2))

    tp = ThreadPool(query_url_list, CON_REQ)


class ThreadPool(object):
    def __init__(self, url_list, thread_num):
        self.work_queue = Queue.Queue()
        self.threads = []
        self.__init_work_queue(url_list)
        self.__init_thread_pool(thread_num)

    def __init_thread_pool(self, thread_num):
        for i in range(thread_num):
            self.threads.append(MyThread(self.work_queue))

    def __init_work_queue(self, url_list):
        for item in url_list:
            self.add_job(do_job, item)

    def add_job(self, func, args):
        self.work_queue.put((func, args))

    def wait_all_complete(self):
        for item in self.threads:
            if item.isAlive():
                item.join()


class MyThread(threading.Thread):
    def __init__(self, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.start()

    def run(self):
        while True:
            try:
                do, args = self.work_queue.get(block=False)
                do(args)
                self.work_queue.task_done() # notify the completement of the job
            except:
                break


def do_job(args):
    try:
        url = args[0]
        qword_obj = args[1]
        sock = urllib2.urlopen(url)
        response = sock.read()
        sock.close()
        if '192.168.0.211' in url:
            source = "makepolo"
        if "1688.com" in url:
            source = "1688"
        query_parser = QueryResultParser(source)
        query_parser.feed(response)
       
        print "query_text: ", qword_obj.query_text, 'href_list length: ', len(query_parser.href_list), 'title_list length: ', len(query_parser.title_list)
        for item in query_parser.href_list:
            print item
        for item in query_parser.title_list:
            print item
        link_and_title = zip(query_parser.href_list, query_parser.title_list)
        link_and_title = link_and_title[:5]  # 只取前5项


        for item in link_and_title:
            print  item[0]
            print item[1]
            QueryItem.objects.create(
                queryword = qword_obj,
                title = item[1],
                href = item[0],
            )
    except Exception, e:
        print e
       

class QueryResultParser(SGMLParser):
    def __init__(self, source):
        self.source = source
        self.is_title = 0
        self.title_text = ""
        self.title_list = []
        self.href_list = []
        SGMLParser.__init__(self)

    def reset(self):
        SGMLParser.reset(self)

    def start_a(self, attrs):
        attr_dict = dict(attrs)
        if self.source == "makepolo":
            if attr_dict.has_key('data-num') and attr_dict['data-num'] == "1":
                self.is_title = 1
                self.href_list.append(attr_dict['href'])
        if self.source == "1688":
            if attr_dict.has_key('offer-stat') and attr_dict['offer-stat'] == "title":
                self.is_title = 1
                self.href_list.append(attr_dict['href'])

    def end_a(self):
        if self.is_title:
            self.is_title = 0
            self.title_text = self.title_text.strip()
            self.title_text = self.title_text.replace('\n', '')
            self.title_text = self.title_text.replace(' ', '')
            self.title_list.append(self.title_text)
            self.title_text = ""

    def handle_data(self, text):
        if self.is_title:
            text = unicode(text, "gbk")
            utf8_text = text.encode('utf-8')
            self.title_text += utf8_text


class GetQueryWordHandler(ListView):
    template_name = 'testtask/relative.html'
    paginate_by = QUERY_WORD_PER_PAGE
    context_object_name = "query_word_list"

    def get_context_data(self, **kwargs):
        context = super(GetQueryWordHandler, self).get_context_data(**kwargs)
        query_words = context['query_word_list']
        query_items = QueryItem.objects.filter(
            queryword = query_words[0],
        )

        context['makepolo_query_item'] = query_items

        return context

    def get_queryset(self):
        #self.task_id = self.request.POST['task_id']
        self.task_id = 16
        query_words = QueryWord.objects.filter(
            task__id=self.task_id,
            source = "makepolo",
        )

        return query_words
