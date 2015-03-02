from django.db import models
from django import forms

class InputForm(forms.Form):
    insertCsv = forms.CharField(max_length=50)
    outCsv1 = forms.CharField(max_length=50)
    outCsv2 = forms.CharField(max_length=50)
    downPath = forms.CharField(max_length=50)
