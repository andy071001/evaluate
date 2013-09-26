#coding=utf8
from django import template
from django.http import HttpResponse ,HttpResponseRedirect
from django.views.generic.base import View
from django.views.generic import ListView
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse

import json
import random
import urllib
import urllib2
import threading
import Queue
import datetime
import xlwt
from sgmllib import SGMLParser

from .models import Task, QueryWord, QueryItem
from .constants import (
    VERIFY_CODE_LENGTH, 
    CON_REQ, 
    online_makepolo_url, 
    strategy_makepolo_url, 
    alibaba_url,
    QUERY_WORD_PER_PAGE,
    QUERY_TASK_PER_PAGE, 
    SHEET_NAME_DICT,
    STRATEGY_RATING_TEXT,
)


register = template.Library()

@register.filter(name='list_iter')
def list_iter(lists):
    list_a, list_b = lists

    for x, y in zip(list_a, list_b):
        yield (x, y)


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
                return HttpResponseRedirect("/testtask/get_query_task")
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
        name = request.POST['name']
        type = int(request.POST['type'])
        file_handler = request.FILES.get('file', None)
        query_text_list = file_handler.readlines()
        process_query(query_text_list, name, type, request.user)
        file_handler.close()
        return HttpResponseRedirect("/testtask/get_query_task")


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
        # online makepolo
        query_url = online_makepolo_url + urllib.quote(item)

        try:
            utf8_item = unicode(item, "gbk").encode("utf8")
        except Exception, e:
            utf8_item = item

        word_item = QueryWord.objects.create(
            task=task, 
            query_text=utf8_item,
        )
        query_url_list.append((query_url, word_item, type))
        
        if (type == 1):  # 相关评估
            # alibaba
            query_url = alibaba_url + urllib.quote(item)
            query_url_list.append((query_url, word_item, type))
        if (type == 2):  # 数据质量评估
            pass  # do nothing, don't need to put url in the query list
        if (type == 3):  # 策略GSB评估
            query_url = strategy_makepolo_url + urllib.quote(item)
            query_url_list.append((query_url, word_item, type))

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
        print "----------->", url
        qword_obj = args[1]
        type = args[2]  # 评估策略类型
        sock = urllib2.urlopen(url)
        response = sock.read()
        sock.close()
        source = ""
        
        if (type == 1 or type == 2):  # 相关性评估 或者 数据质量评估
            if online_makepolo_url in url:
                source = "online_makepolo"
            if alibaba_url in url:
                source = "alibaba"

        if (type == 3):
            print "###" * 20
            print "strategy"
            print strategy_makepolo_url
            print "online"
            print online_makepolo_url
            print "current"
            print url
            if strategy_makepolo_url in url:
                source = "strategy_makepolo"
            elif online_makepolo_url in url:
                source = "online_makepolo"
        query_parser = QueryResultParser(source, type)
        query_parser.feed(response)
       

        link_and_title = zip(query_parser.href_list, query_parser.title_list)
        link_and_title = link_and_title[:5]  # 只取前5项

        for item in link_and_title:
            QueryItem.objects.create(
                queryword = qword_obj,
                source = source,
                title = item[1],
                href = item[0],
            )
    except Exception, e:
        print e
       

class QueryResultParser(SGMLParser):
    def __init__(self, source, type):
        self.source = source
        self.type = type
        self.is_title = 0
        self.title_text = ""
        self.title_list = []
        self.href_list = []
        SGMLParser.__init__(self)

    def reset(self):
        SGMLParser.reset(self)

    def start_a(self, attrs):
        attr_dict = dict(attrs)
        if attr_dict.has_key('data-num') and attr_dict['data-num'] == "1":
            self.is_title = 1
            self.href_list.append(attr_dict['href'])

        if self.type == 1:  # 相关
            if self.source == "alibaba":
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
    template_name = "testtask/relative.html"
    paginate_by = QUERY_WORD_PER_PAGE
    context_object_name = "query_word_list"

    #def get_template_names(self):
    #    try:
    #        self.task_id = self.request.GET['task_id']
    #    except:
    #        self.task_id = 1
    #    temp_task = Task.objects.get(id=self.task_id)
    #    if (temp_task.type == 1 or 2):
    #        return ['testtask/relative.html']
    #    if (temp_task.type == 3):
    #        return ['testtask/strategy.html']

    def get_context_data(self, **kwargs):
        context = super(GetQueryWordHandler, self).get_context_data(**kwargs)
        query_words = context['query_word_list']
        try:
            query_word_seq = int(self.request.GET['query_word_seq'])
        except:
            query_word_seq = 0

        #if self.query_word_text:
        #    type = query_words
        print "*" * 50
        print "query_words: ", query_words
        print "*" * 50
        type = query_words[query_word_seq].task.type
        context['type'] = type
        context['query_word_name'] = query_words[query_word_seq].query_text
        context['type_name'] = SHEET_NAME_DICT[type-1]
        the_task = Task.objects.get(id=self.task_id)
        context['task_total_num'] = the_task.number
        context['task_left_num'] = the_task.number - the_task.complete
        context['task_id'] = self.task_id

        makepolo_query_items = []
        alibaba_query_items = []
        if query_words:
            makepolo_query_items = QueryItem.objects.filter(
                queryword = query_words[query_word_seq],
                source = "online_makepolo",
            )

            if type == 1:  # 相关
                alibaba_query_items = QueryItem.objects.filter(
                    queryword = query_words[query_word_seq],
                    source = "alibaba",
                )
                print "*"*30
                print "makepolo items:"
                print makepolo_query_items
                print alibaba_query_items
                context['query_item'] = map(lambda *row: list(row) , makepolo_query_items, alibaba_query_items)
                print "query_item:  "
                print context["query_item"]
            if type == 3:  # 策略
                strategy_query_items = QueryItem.objects.filter(
                    queryword = query_words[query_word_seq],
                    source = "strategy_makepolo",
                )
                context['query_item'] = map(lambda *row: list(row) , makepolo_query_items, strategy_query_items)

            if type == 2:  # 质量
                context['query_item'] = makepolo_query_items
                print "@@@@@"* 80
                print context["query_item"]

        context['query_word_item'] = query_words[query_word_seq]
        #context['next_word_seq'] = query_word_seq + 1
        #contxt['prev_word_seq'] = query_word_seq - 1

        #if (context['prev_word_seq'] < 0)
        #    context['prev_word_seq'] = 0
        #if (context['next_word_seq'] >= QUERY_WORD_PER_PAGE)
        #    context['next_word_seq'] = QUERY_WORD_PER_PAGE - 1

        # context['query_item'] = map(None, makepolo_query_items, alibaba_query_items)
        context['query_word_seq'] = query_word_seq
        context['last_word_seq'] = len(query_words) - 1
        return context

    def get_queryset(self):
        try:
            self.task_id = self.request.GET['task_id']
        except:
            self.task_id = 1

        try:
            self.query_word_text = self.request.GET['search_word']
        except:
            self.query_word_text = None
        # self.task_id = 1
        if self.query_word_text:
            query_words = QueryWord.objects.filter(
                task__id=self.task_id,
                query_text=self.query_word_text,
            )
        else:
            query_words = QueryWord.objects.filter(
                task__id=self.task_id,
            )

        return query_words


def get_or_none(post_dict, key):
    try:
        return post_dict[key]
    except:
        return ""

def get_or_false(post_dict, key):
    try:
        return post_dict[key]
    except:
        return False

class SetBadReasonHandler(View):
    def post(self, request):
        query_item_id = get_or_none(request.POST, 'query_item_id')
        note = get_or_none(request.POST, 'note')
        is_business = get_or_false(request.POST, 'is_business')
        is_free = get_or_false(request.POST, 'is_free')
        rating = get_or_none(request.POST, 'rating')

        deadlink = get_or_none(request.POST, 'deadlink')
        repeat = get_or_none(request.POST, 'repeat')
        change = get_or_none(request.POST, 'change')
        keyword = get_or_none(request.POST, 'keyword')
        cutword = get_or_none(request.POST, 'cutword')
        lowquality = get_or_none(request.POST, 'lowquality')
        noimage = get_or_none(request.POST, 'noimage')
        lessthan5 = get_or_none(request.POST, 'lessthan5')

        if query_item_id: 
            query_item = QueryItem.objects.get(id=query_item_id)

            if note:
                query_item.note = note
            if is_business:
                query_item.is_business = is_business
            if is_free:
                query_item.is_free = is_free
            if rating:
                query_item.rating = rating

            query_item.deadlink = deadlink
            query_item.repeat = repeat
            query_item.change = change
            query_item.keyword = keyword
            query_item.cutword = cutword
            query_item.lowquality = lowquality
            query_item.noimage = noimage
            query_item.lessthan5 = lessthan5
            query_item.is_complete = True

            query_item.save()

            query_word_item = query_item.queryword
            relate_query_task = query_word_item.task
            relate_query_items = QueryItem.objects.filter(queryword=query_word_item)
            counter = 0
            total_item_num = len(relate_query_items)
            for r_item in relate_query_items:
                if r_item.is_complete:
                    counter += 1

            if total_item_num == counter:
                query_word_item.is_complete = True

            query_word_item.save()

            relate_query_word_items = QueryWord.objects.filter(task=relate_query_task)
            total_query_item_num = len(relate_query_word_items)

            w_counter = 0
            for r_q_item in relate_query_word_items:
                if r_q_item.is_complete:
                    w_counter += 1
            relate_query_task.complete = w_counter
            if w_counter == total_query_item_num:
                relate_query_task.is_complete = True

            relate_query_task.save()

            data = {}
            data['status'] = "success"
            data["info"] = "更新成功"

            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data = {}
            data['status'] = "failure"
            data["info"] = "更新失败"
            return HttpResponse(json.dumps(data), content_type="application/json")


class GetQueryTaskHandler(ListView):
    template_name = 'testtask/task_query.html'
    paginate_by = QUERY_TASK_PER_PAGE
    context_object_name = "query_task_list"

    def get_context_data(self, **kwargs):
        context = super(GetQueryTaskHandler, self).get_context_data(**kwargs)
        return context

    def get_queryset(self):
        tasks = Task.objects.filter(is_delete=False)
        return tasks


class DeleteTaskHandler(ListView):
    def post(self, request):
        task_id = request.POST['task_id']
        task = Task.objects.get(id=task_id)
        task.is_delete = True
        task.save()

        data = {}
        data['status'] = "success"
        data["info"] = "更新成功"

        return HttpResponse(json.dumps(data), content_type="application/json")


class AddWordNoteHandler(View):
    def get(self, request):
        word_item_id = self.request.GET['word_id']
        word_note = self.request.GET['word_note']
        word_item = QueryWord.objects.get(id=word_item_id)
        if word_item.task.type == 3:  # 策略评估需要添加评价
            word_item.score = self.request.GET['qword_rating']
        word_item.note = word_note
        word_item.save()

        last = get_or_none(self.request.GET, 'last')
        next = get_or_none(self.request.GET, 'next')
        current_task_id = word_item.task.id
        query_word_seq = self.request.GET['query_word_seq']
        current_page = self.request.GET['current_page']
        if last:
            current_word_seq = int(query_word_seq) - 1 
        elif next:
            current_word_seq = int(query_word_seq) + 1 

        return HttpResponseRedirect('/testtask/get_query_word?page=%s&query_word_seq=%s&task_id=%s' % (current_page, current_word_seq, current_task_id))


rel_header = ['query', 'seq', 'title', 'url', 'score', 'comment', 
              '          ', 'seq', 'title', 'url', 'score', 'comment',
              '          ', '总comment', 'username',]

quality_header = ['query', 'seq', 'title', 'url', 'score', 'comment', 
                    '          ', '总comment', 'username',]

strategy_header = ['query', 'seq', 'title', 'url',
              '          ', 'seq', 'title', 'url', 'score', 
              '          ', '总comment', 'username',]

header_list = [rel_header, quality_header, strategy_header]

def get_comment_string_for_xls(item):
    s = ""
    if item.deadlink == "checked":
        s += u"死链  "
    if item.repeat == "checked":
        s += u"公司重复  "
    if item.change == "checked":
        s += u"含义转变  "
    if item.keyword == "checked":
        s += u"出现部分关键字  "
    if item.cutword == "checked":
        s += u"切词七零八落  "
    if item.lowquality== "checked":
        s += u"低质量内容页  "
    if item.noimage== "checked":
        s += u"无图片  "
    if item.lessthan5 == "checked":
        s += u"结果数少于5    "

    if item.note:
        s += item.note

    return s

class OutputToExcelHandler(View):
    def get(self, request):
        task_id = request.GET['task_id']
        task = Task.objects.get(id=task_id)

        book = xlwt.Workbook(encoding='utf8')
        sheet_name = SHEET_NAME_DICT[task.type-1]
        sheet = book.add_sheet(sheet_name)
        #default_style = xlwt.Style.default_style
        #default_style = xlwt.easyxf('align: wrap on')
        default_style = xlwt.easyxf('align: vertical center, horizontal center;') 

        query_words = QueryWord.objects.filter(task=task)
        current_header = header_list[task.type-1]
        
        for idx, item in enumerate(current_header):
            sheet.write(0, idx, item, style=default_style)

        if task.type == 1:  # 相关
            cur_row = 1
            for row1, item in enumerate(query_words):
                makepolo_query_items = QueryItem.objects.filter(
                    queryword=item,
                    source="online_makepolo",
                )
                
                alibaba_query_items = QueryItem.objects.filter(
                    queryword=item,
                    source="alibaba",
                )
                query_item = map(lambda *row: list(row) , makepolo_query_items, alibaba_query_items)

                if item.note:
                    sheet.write(cur_row, 13, item.note, style=default_style)
                sheet.write(cur_row, 14, task.creator.username, style=default_style)

                counter = 0
                 
                for m_item, a_item in query_item:
                    if m_item:
                        sheet.write(cur_row, 0, item.query_text, style=default_style)
                        sheet.write(cur_row, 1, counter+1, style=default_style)
                        sheet.write(cur_row, 2, m_item.title, style=default_style)
                        sheet.write(cur_row, 3, m_item.href, style=default_style)
                        sheet.write(cur_row, 4, m_item.rating, style=default_style)
                        
                        s =  get_comment_string_for_xls(m_item)
                        sheet.write(cur_row, 5, s, style=default_style)
                    
                    if a_item:
                        sheet.write(cur_row, 7, counter+1, style=default_style)
                        sheet.write(cur_row, 8, a_item.title, style=default_style)
                        sheet.write(cur_row, 9, a_item.href, style=default_style)
                        sheet.write(cur_row, 10, a_item.rating, style=default_style)
                        
                        s =  get_comment_string_for_xls(a_item)
                        sheet.write(cur_row, 11, s, style=default_style)

                    counter += 1
                    cur_row += 1

        if task.type == 2:  # 数据质量
            cur_row = 1
            for row1, item in enumerate(query_words):
                makepolo_query_items = QueryItem.objects.filter(
                    queryword=item,
                    source="online_makepolo",
                )

                if item.note:
                    sheet.write(cur_row, 7, item.note, style=default_style)
                sheet.write(cur_row, 8, task.creator.username, style=default_style)

                counter = 0
                 
                for m_item in makepolo_query_items:
                    if m_item:
                        sheet.write(cur_row, 0, item.query_text, style=default_style)
                        sheet.write(cur_row, 1, counter+1, style=default_style)
                        sheet.write(cur_row, 2, m_item.title, style=default_style)
                        sheet.write(cur_row, 3, m_item.href, style=default_style)
                        sheet.write(cur_row, 4, m_item.rating, style=default_style)
                        
                        s =  get_comment_string_for_xls(m_item)
                        sheet.write(cur_row, 5, s, style=default_style)
                    
                    counter += 1
                    cur_row += 1

        if task.type == 3:  # 策略
            print "*********************************************"
            print "in type = 3"
            cur_row = 1
            for row1, item in enumerate(query_words):
                makepolo_query_items = QueryItem.objects.filter(
                    queryword=item,
                    source="online_makepolo",
                )
                
                strategy_query_items = QueryItem.objects.filter(
                    queryword=item,
                    source="strategy_makepolo",
                )
                query_item = map(lambda *row: list(row) , makepolo_query_items, strategy_query_items)

                if item.note:
                    sheet.write(cur_row, 10, item.note, style=default_style)
                    sheet.write(cur_row, 11, task.creator.username, style=default_style)
                if item.score:
                    print "^^^^^^^^^^^%%%%%" * 20
                    print item.score
                    sheet.write(cur_row, 8, STRATEGY_RATING_TEXT[item.score], style=default_style)

                counter = 0
                 
                for m_item, a_item in query_item:
                    if m_item:
                        sheet.write(cur_row, 0, item.query_text, style=default_style)
                        sheet.write(cur_row, 1, counter+1, style=default_style)
                        sheet.write(cur_row, 2, m_item.title, style=default_style)
                        sheet.write(cur_row, 3, m_item.href, style=default_style)
                    
                    if a_item:
                        sheet.write(cur_row, 5, counter+1, style=default_style)
                        sheet.write(cur_row, 6, a_item.title, style=default_style)
                        sheet.write(cur_row, 7, a_item.href, style=default_style)
                        

                    counter += 1
                    cur_row += 1

        response = HttpResponse(mimetype='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=example.xls'
        book.save(response)

        return response


class CopyTaskHandler(View):
    def post(self, request):
        task_id = get_or_none(self.request.POST, 'task_id')
        data = {}

        if task_id:
            task = Task.objects.get(id=task_id)
            t_id = task.id
            task.creator = request.user  # change creator to the current user
            task.pk = None
            task.create_time = datetime.datetime.now()
            task.save()  # save task

            query_words = QueryWord.objects.filter(task__id=t_id)
            for q_word in query_words:
                q_id = q_word.id
                q_word.pk = None
                q_word.task = task
                q_word.save()  # save query word
                makepolo_query_items = QueryItem.objects.filter(queryword__id=q_id, source="online_makepolo")
                for m_item in makepolo_query_items:
                    m_item.pk = None
                    m_item.queryword = q_word
                    m_item.save()  # save query item

                if task.type == 1:  # 相关性评估
                    alibaba_query_items = QueryItem.objects.filter(queryword__id=q_id, source="alibaba")
                    for a_item in alibaba_query_items:
                        a_item.pk = None
                        a_item.queryword = q_word
                        a_item.save()

                if task.type == 3:  # 策略评估
                    strategy_query_items = QueryItem.objects.filter(queryword__id=q_id, source="strategy_makepolo")
                    for s_item in strategy_query_items:
                        s_item.pk = None
                        s_item.queryword = q_word
                        s_item.save()  # save query item

            data['status'] = "success"
            data["info"] = "更新成功"

            return HttpResponse(json.dumps(data), content_type="application/json")

        data['status'] = "failure"
        data["info"] = "更新失败"

        return HttpResponse(json.dumps(data), content_type="application/json")
