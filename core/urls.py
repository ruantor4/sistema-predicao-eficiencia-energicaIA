from django.urls import path

from core.views import HomeView

urlpatterns = [

    # Rota página inicial
    path('', HomeView.as_view(), name='home'),

]
