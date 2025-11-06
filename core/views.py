from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views import View

class HomeView(LoginRequiredMixin, View):

    login_url = '/login/'
    def get(self, request:HttpRequest) -> HttpResponse:
        return render(request, 'core/home.html')

