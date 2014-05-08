# -*- coding: utf-8 -*-
import logging
from django import template
import  django.template.defaultfilters as defaultfilters
import urllib
register = template.Library()
from datetime import *

@register.filter
def datetz(date,format):  #datetime with timedelta
	t=timedelta(seconds=3600)
	return defaultfilters.date(date+t,format)
