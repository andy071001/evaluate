#encoding=utf-8
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Task(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User)
    create_time = models.DateTimeField(max_length=50)
    number = models.IntegerField(default=0)
    complete = models.IntegerField(default=0)
    state = models.BooleanField(default=False)
    type = models.IntegerField()


class QueryWord(models.Model):
    task = models.ForeignKey(Task)
    source = models.CharField(max_length=30)
    query_text = models.CharField(max_length=100)


class QueryItem(models.Model):
    queryword = models.ForeignKey(QueryWord)
    title = models.CharField(max_length=1000)
    href = models.CharField(max_length=2048)
    rating = models.IntegerField(blank=True, null=True)
    reason =  models.IntegerField(blank=True, null=True)  # bit位表示选项
    note = models.CharField(max_length=100, blank=True, null=True)
    is_business = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
