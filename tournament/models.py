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
        for team in [self.home_team, self.away_team]:
            team.played = 0
            team.won = 0
            team.drawn = 0
            team.lost = 0
            team.goals_for = 0
            team.goals_against = 0
            team.points = 0

        finished_matches = Match.objects.filter(status='finished')

        for match in finished_matches:
            match.home_team.played += 1
            match.home_team.goals_for += match.home_score
            match.home_team.goals_against += match.away_score

            match.away_team.played += 1
            match.away_team.goals_for += match.away_score
            match.away_team.goals_against += match.home_score

            if match.home_score > match.away_score:
                match.home_team.won += 1
                match.home_team.points += 3
                match.away_team.lost += 1
            elif match.home_score < match.away_score:
                match.away_team.won += 1
                match.away_team.points += 3
                match.home_team.lost += 1
            else:
                match.home_team.drawn += 1
                match.away_team.drawn += 1
                match.home_team.points += 1
                match.away_team.points += 1

        for team in Team.objects.all():
            team.save()


class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals_scored')

    class Meta:
        ordering = ['match', 'id']

    def __str__(self):
        return f"{self.player.name} - {self.match}"
