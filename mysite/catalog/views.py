from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

def main(request: HttpRequest):
    return HttpResponse('H')