
from datetime import datetime, date
from django.http import HttpResponse
from models import Task, QueryWord, QueryItem
import xlwt

book = xlwt.Workbook(encoding='utf8')
sheet = book.add_sheet('untitled')

default_style = xlwt.Style.default_style
datetime_style = xlwt.easyxf(num_format_str='dd-mm-yyyy hh:mm')
date_style = xlwt.easyxf(num_format_str='dd-mm-yyyy')

values_list = Task.objects.all().values_list()

for row, rowdata in enumerate(values_list):
    for col, val in enumerate(rowdata):
        if isinstance(val, datetime):
            style = datetme_style
        elif isinstance(val, date):
            style = date_style
        else:
            style = default_style

        sheet.write(row, col, val, style=style)

response = HttpResponse(mimetype='application/vnd.ms-excel')
response['Content-Disposition'] = 'attachment; filename=example.xls')
book.save(response)
return response
