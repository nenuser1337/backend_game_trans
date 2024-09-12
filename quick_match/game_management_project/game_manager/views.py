# game_manager/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Player, QuickMatch, Tournament, TournamentMatch
import json
from django.db import models

def home(request):
    return render(request, 'home.html', {'show_history_link': True})

def quickmatch_form(request):
    if request.method == 'POST':
        player1_name = request.POST['player1']
        player2_name = request.POST['player2']
        
        player1, _ = Player.objects.get_or_create(name=player1_name)
        player2, _ = Player.objects.get_or_create(name=player2_name)
        
        match = QuickMatch.objects.create(player1=player1, player2=player2)
        
        return redirect(reverse('quickmatch_result', kwargs={'match_id': match.id}))
    
    return render(request, 'quickmatch_form.html')

def quickmatch_result(request, match_id):
    match = get_object_or_404(QuickMatch, id=match_id)
    
    if request.method == 'POST':
        winner_id = request.POST['winner']
        winner = Player.objects.get(id=winner_id)
        match.winner = winner
        match.save()
        messages.success(request, f"{winner.name} has won the QuickMatch!")
        return redirect('quickmatch_result', match_id=match.id)
    
    return render(request, 'quickmatch_result.html', {'match': match})

@require_POST
@csrf_exempt
def quickmatch_select_winner(request, match_id):
    match = get_object_or_404(QuickMatch, id=match_id)
    data = json.loads(request.body)
    winner_id = data.get('winner_id')
    
    if winner_id:
        winner = get_object_or_404(Player, id=winner_id)
        match.winner = winner
        match.save()
        return JsonResponse({'status': 'success', 'winner_name': winner.name})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid winner ID'})

def create_tournament(request):
    if request.method == 'POST':
        tournament_name = request.POST['tournament_name']
        player_names = request.POST.getlist('player_names')
        
        tournament = Tournament.objects.create(name=tournament_name)
        
        for name in player_names:
            player, _ = Player.objects.get_or_create(name=name.strip())
            tournament.players.add(player)
        
        messages.success(request, f"Tournament '{tournament.name}' created successfully with {tournament.players.count()} players.")
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    return render(request, 'tournament_form.html')

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    return render(request, 'tournament_detail.html', {'tournament': tournament})

def tournament_bracket(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.get_status() == "Not Started":
        messages.warning(request, "This tournament hasn't started yet.")
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    current_matches = tournament.get_current_matches()
    
    return render(request, 'tournament_bracket.html', {
        'tournament': tournament,
        'current_matches': current_matches,
    })

@require_POST
@csrf_exempt
def tournament_select_winner(request, tournament_id, match_id):
    match = get_object_or_404(TournamentMatch, id=match_id, tournament_id=tournament_id)
    tournament = match.tournament
    data = json.loads(request.body)
    winner_id = data.get('winner_id')
    
    if winner_id:
        winner = get_object_or_404(Player, id=winner_id)
        match.winner = winner
        match.save()
        
        tournament.advance_winners()
        
        if tournament.is_concluded:
            return JsonResponse({
                'status': 'success',
                'winner_name': winner.name,
                'tournament_concluded': True,
                'tournament_winner': tournament.winner.name
            })
        else:
            return JsonResponse({'status': 'success', 'winner_name': winner.name})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid winner ID'})

def match_history(request):
    quick_matches = QuickMatch.objects.all().order_by('-created_at')
    tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'match_history.html', {'quick_matches': quick_matches, 'tournaments': tournaments})

def tournament_results(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = TournamentMatch.objects.filter(tournament=tournament).order_by('round', 'id')
    
    matches_data = []
    for match in matches:
        matches_data.append({
            'round': match.round,
            'player1': match.player1.name,
            'player2': match.player2.name if match.player2 else 'Bye',
            'result': match.get_result_display()
        })
    
    return render(request, 'tournament_results.html', {
        'tournament': tournament,
        'matches': matches_data
    })

def start_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if request.method == 'POST':
        if tournament.players.count() >= 2:
            tournament.start_tournament()
            messages.success(request, f"Tournament '{tournament.name}' has started!")
        else:
            messages.error(request, "Not enough players to start the tournament.")
    return redirect('tournament_detail', tournament_id=tournament.id)

def play_pong(request, match_type, match_id):
    if match_type == 'quick':
        match = get_object_or_404(QuickMatch, id=match_id)
    else:  # tournament match
        match = get_object_or_404(TournamentMatch, id=match_id)
    
    return render(request, 'play_pong.html', {
        'match': match,
        'match_type': match_type,
    })

@require_POST
@csrf_exempt
def update_match_score(request, match_type, match_id):
    if match_type == 'quick':
        match = get_object_or_404(QuickMatch, id=match_id)
    else:  # tournament match
        match = get_object_or_404(TournamentMatch, id=match_id)
    
    data = json.loads(request.body)
    match.player1_score = data.get('player1_score', 0)
    match.player2_score = data.get('player2_score', 0)
    
    if match.player1_score > match.player2_score:
        match.winner = match.player1
    elif match.player2_score > match.player1_score:
        match.winner = match.player2
    
    match.save()

    if match_type == 'tournament':
        tournament = match.tournament
        tournament.advance_winners()

    return JsonResponse({
        'status': 'success', 
        'winner_name': match.winner.name if match.winner else None,
        'player1_score': match.player1_score,
        'player2_score': match.player2_score
    })
    
def join_tournament(request):
    if request.method == 'POST':
        tournament_id = request.POST.get('tournament_id')
        player_name = request.POST.get('player_name')
        
        tournament = get_object_or_404(Tournament, id=tournament_id)
        
        if tournament.can_join():
            player, created = Player.objects.get_or_create(name=player_name)
            tournament.players.add(player)
            messages.success(request, f"You have successfully joined the tournament: {tournament.name}")
        else:
            messages.error(request, "This tournament cannot be joined at this time.")
        
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    open_tournaments = Tournament.objects.filter(is_ongoing=False, is_concluded=False)
    return render(request, 'join_tournament.html', {'tournaments': open_tournaments})    

def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'tournament_list.html', {'tournaments': tournaments})