from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic import ListView
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login

import random
from .constants import VERIFY_CODE_LENGTH


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
        file_handler = request.FILES.get('file', None)
        file_obj = file_handler.read()
        return HttpResponse("good")
