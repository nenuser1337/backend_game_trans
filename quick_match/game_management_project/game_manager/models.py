# game_manager/models.py

from django.db import models
from django.utils import timezone
import random

class Player(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class QuickMatch(models.Model):
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='quickmatch_player1')
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='quickmatch_player2')
    winner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='quickmatch_winner', null=True, blank=True)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player1} vs {self.player2}"

    def get_result_display(self):
        if self.winner:
            return f"{self.winner.name} won against {self.player2.name if self.winner == self.player1 else self.player1.name} ({self.player1_score}-{self.player2_score})"
        return "Match not completed"

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    players = models.ManyToManyField(Player)
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='tournament_winner', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_concluded = models.BooleanField(default=False)
    is_ongoing = models.BooleanField(default=False)
    current_round = models.IntegerField(default=1)
    start_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_status(self):
        if self.is_concluded:
            return "Concluded"
        elif self.is_ongoing:
            return "Ongoing"
        else:
            return "Not Started"

    def generate_matches(self):
        players = list(self.players.all())
        random.shuffle(players)
        num_players = len(players)
        
        for i in range(0, num_players, 2):
            if i + 1 < num_players:
                TournamentMatch.objects.create(
                    tournament=self,
                    player1=players[i],
                    player2=players[i+1],
                    round=1
                )
            else:
                TournamentMatch.objects.create(
                    tournament=self,
                    player1=players[i],
                    player2=None,
                    round=1,
                    winner=players[i]
                )

    def advance_winners(self):
        current_matches = self.tournamentmatch_set.filter(round=self.current_round)
        
        if all(match.winner for match in current_matches):
            winners = [match.winner for match in current_matches]
            
            if len(winners) == 1:
                self.winner = winners[0]
                self.is_concluded = True
                self.is_ongoing = False
                self.save()
                return
            
            self.current_round += 1
            self.save()
            
            for i in range(0, len(winners), 2):
                if i + 1 < len(winners):
                    TournamentMatch.objects.create(
                        tournament=self,
                        player1=winners[i],
                        player2=winners[i+1],
                        round=self.current_round
                    )
                else:
                    TournamentMatch.objects.create(
                        tournament=self,
                        player1=winners[i],
                        player2=None,
                        round=self.current_round,
                        winner=winners[i]
                    )

    def get_current_matches(self):
        return self.tournamentmatch_set.filter(round=self.current_round)

    def get_result_summary(self):
        if self.is_concluded:
            return f"Tournament concluded. Winner: {self.winner.name}"
        elif self.is_ongoing:
            return f"Tournament in progress. Current round: {self.current_round}"
        else:
            return "Tournament not started"

    def can_join(self):
        return not self.is_ongoing and not self.is_concluded

    def start_tournament(self):
        if not self.is_ongoing and self.players.count() >= 2:
            self.is_ongoing = True
            self.start_date = timezone.now()
            self.save()
            self.generate_matches()

class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='tournamentmatch_player1')
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='tournamentmatch_player2', null=True, blank=True)
    winner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='tournamentmatch_winner', null=True, blank=True)
    round = models.IntegerField()
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tournament.name}: {self.player1} vs {self.player2 or 'Bye'} (Round {self.round})"

    def get_display_name(self):
        if self.player2:
            return f"{self.player1.name} vs {self.player2.name}"
        else:
            return f"{self.player1.name} (Bye)"
        
    def get_result_display(self):
        if self.winner:
            if self.player2:
                return f"{self.winner.name} won against {self.player2.name if self.winner == self.player1 else self.player1.name} ({self.player1_score}-{self.player2_score})"
            else:
                return f"{self.winner.name} advanced (Bye)"
        elif not self.player2:
            return f"{self.player1.name} to advance (Bye)"
        return "Match not completed"

    def set_winner(self):
        if self.player1_score > self.player2_score:
            self.winner = self.player1
        elif self.player2_score > self.player1_score:
            self.winner = self.player2
        self.save()