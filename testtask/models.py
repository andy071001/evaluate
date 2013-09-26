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
    is_delete = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)


class QueryWord(models.Model):
    task = models.ForeignKey(Task)
    query_text = models.CharField(max_length=100)
    note = models.CharField(max_length=1000)
    score = models.IntegerField(default=2, blank=True, null=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('task', 'query_text',)


class QueryItem(models.Model):
    queryword = models.ForeignKey(QueryWord)
    source = models.CharField(max_length=30)
    title = models.CharField(max_length=1000)
    href = models.CharField(max_length=2048)
    rating = models.IntegerField(blank=True, null=True)
    note = models.CharField(max_length=100, blank=True, null=True)
    is_business = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    deadlink = models.CharField(max_length=30)
    repeat = models.CharField(max_length=30)
    change = models.CharField(max_length=30)
    keyword = models.CharField(max_length=30)
    cutword = models.CharField(max_length=30)
    lowquality = models.CharField(max_length=30)
    noimage = models.CharField(max_length=30)
    lessthan5 = models.CharField(max_length=30)

    
