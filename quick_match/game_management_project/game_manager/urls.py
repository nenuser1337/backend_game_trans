from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('quickmatch/', views.quickmatch_form, name='quickmatch_form'),
    path('quickmatch/<int:match_id>/', views.quickmatch_result, name='quickmatch_result'),
    path('quickmatch/<int:match_id>/select-winner/', views.quickmatch_select_winner, name='quickmatch_select_winner'),
    path('tournament/create/', views.create_tournament, name='create_tournament'),
    path('tournament/join/', views.join_tournament, name='join_tournament'),  # Add this line
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('tournament/<int:tournament_id>/bracket/', views.tournament_bracket, name='tournament_bracket'),
    path('tournament/<int:tournament_id>/start/', views.start_tournament, name='start_tournament'),
    path('tournament/<int:tournament_id>/<int:match_id>/select-winner/', views.tournament_select_winner, name='tournament_select_winner'),
    path('match-history/', views.match_history, name='match_history'),
    path('tournament/<int:tournament_id>/results/', views.tournament_results, name='tournament_results'),
    path('play-pong/<str:match_type>/<int:match_id>/', views.play_pong, name='play_pong'),
    path('update-score/<str:match_type>/<int:match_id>/', views.update_match_score, name='update_match_score'),
    path('tournaments/', views.tournament_list, name='tournament_list'),
]