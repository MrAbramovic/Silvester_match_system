from django.urls import path
from . import views

app_name = 'tournament'

urlpatterns = [
    path('', views.home, name='home'),
    path('fixtures/', views.fixtures, name='fixtures'),
    path('results/', views.results, name='results'),
    path('standings/', views.standings, name='standings'),
    path('top-scorers/', views.top_scorers, name='top_scorers'),
    path('match/<int:match_id>/', views.match_detail, name='match_detail'),
]
