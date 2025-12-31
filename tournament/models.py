from django.core.validators import MinValueValidator
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    group = models.CharField(max_length=10, choices=[
        ('A', 'Group A'),
        ('B', 'Group B'),
        ('C', 'Group C'),
        ('D', 'Group D'),
    ], default='A')
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)

    # Statistics calculated from matches
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    class Meta:
        ordering = ['group', '-points', '-goals_for']

    def __str__(self):
        return self.name

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against


class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')

    class Meta:
        ordering = ['team', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name})"

    @property
    def goal_count(self):
        return self.goals.count()


class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('finished', 'Finished'),
    ]

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    away_score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    group = models.CharField(max_length=10, blank=True)
    stage = models.CharField(max_length=50, default='Group Stage')
    match_order = models.IntegerField(default=0)
    match_time = models.TimeField(null=True, blank=True, help_text='Match start time')  # ADD THIS LINE

    class Meta:
        ordering = ['match_order', 'id']
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"

    def save(self, *args, **kwargs):
        if not self.group and self.home_team.group == self.away_team.group:
            self.group = self.home_team.group
        super().save(*args, **kwargs)

        if self.status == 'finished':
            self.update_team_stats()

    def update_team_stats(self):
        """Update team statistics based on match result"""
        from django.db.models import Q

        # Reset ALL team stats to zero first
        Team.objects.all().update(
            played=0,
            won=0,
            drawn=0,
            lost=0,
            goals_for=0,
            goals_against=0,
            points=0
        )

        # Get all finished group stage matches
        # Handle multiple stage format possibilities
        finished_matches = Match.objects.filter(
            status='finished'
        ).filter(
            Q(stage__icontains='group') |
            Q(stage='group_stage') |
            Q(stage='Group Stage')
        )

        print(f"Found {finished_matches.count()} finished group stage matches")  # Debug

        # Build stats dictionary for each team
        team_stats = {}

        for match in finished_matches:
            print(f"Processing: {match.home_team.name} {match.home_score}-{match.away_score} {match.away_team.name}")  # Debug

            # Initialize team stats if not exists
            if match.home_team.id not in team_stats:
                team_stats[match.home_team.id] = {
                    'team': match.home_team,
                    'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                    'goals_for': 0, 'goals_against': 0, 'points': 0
                }
            if match.away_team.id not in team_stats:
                team_stats[match.away_team.id] = {
                    'team': match.away_team,
                    'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                    'goals_for': 0, 'goals_against': 0, 'points': 0
                }

            # Update played count
            team_stats[match.home_team.id]['played'] += 1
            team_stats[match.away_team.id]['played'] += 1

            # Update goals
            team_stats[match.home_team.id]['goals_for'] += match.home_score
            team_stats[match.home_team.id]['goals_against'] += match.away_score
            team_stats[match.away_team.id]['goals_for'] += match.away_score
            team_stats[match.away_team.id]['goals_against'] += match.home_score

            # Update win/draw/loss and points
            if match.home_score > match.away_score:
                team_stats[match.home_team.id]['won'] += 1
                team_stats[match.home_team.id]['points'] += 3
                team_stats[match.away_team.id]['lost'] += 1
            elif match.home_score < match.away_score:
                team_stats[match.away_team.id]['won'] += 1
                team_stats[match.away_team.id]['points'] += 3
                team_stats[match.home_team.id]['lost'] += 1
            else:
                team_stats[match.home_team.id]['drawn'] += 1
                team_stats[match.home_team.id]['points'] += 1
                team_stats[match.away_team.id]['drawn'] += 1
                team_stats[match.away_team.id]['points'] += 1

        # Save all team stats
        for team_id, stats in team_stats.items():
            team = stats['team']
            team.played = stats['played']
            team.won = stats['won']
            team.drawn = stats['drawn']
            team.lost = stats['lost']
            team.goals_for = stats['goals_for']
            team.goals_against = stats['goals_against']
            team.points = stats['points']
            team.save()
            print(f"Updated {team.name}: {team.points} points")  # Debug


class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals_scored')

    class Meta:
        ordering = ['match', 'id']

    def __str__(self):
        return f"{self.player.name} - {self.match}"
