# game_manager/admin.py

from django.contrib import admin
from .models import Player, QuickMatch, Tournament, TournamentMatch

admin.site.register(Player)
admin.site.register(QuickMatch)
admin.site.register(Tournament)
admin.site.register(TournamentMatch)