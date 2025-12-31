from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .models import Goal, Match, Player, Team


def home(request):
    upcoming_matches = Match.objects.filter(status='scheduled')[:6]
    recent_matches = Match.objects.filter(status='finished').order_by('-id')[:6]

    context = {
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
    }
    return render(request, 'tournament/home.html', context)


def fixtures(request):
    group = request.GET.get('group', '')
    stage = request.GET.get('stage', '')

    matches = Match.objects.all()

    if group:
        matches = matches.filter(group=group)
    if stage:
        matches = matches.filter(stage=stage)

    groups = ['A', 'B', 'C', 'D']
    stages = Match.objects.values_list('stage', flat=True).distinct()

    context = {
        'matches': matches,
        'groups': groups,
        'stages': stages,
        'selected_group': group,
        'selected_stage': stage,
    }
    return render(request, 'tournament/fixtures.html', context)


def results(request):
    group = request.GET.get('group', '')
    stage = request.GET.get('stage', '')

    matches = Match.objects.filter(status='finished')

    if group:
        matches = matches.filter(group=group)
    if stage:
        matches = matches.filter(stage=stage)

    groups = ['A', 'B', 'C', 'D']
    stages = Match.objects.values_list('stage', flat=True).distinct()

    context = {
        'matches': matches,
        'groups': groups,
        'stages': stages,
        'selected_group': group,
        'selected_stage': stage,
    }
    return render(request, 'tournament/results.html', context)


def standings(request):
    groups = {}
    for group_letter in ['A', 'B', 'C', 'D']:
        teams = Team.objects.filter(group=group_letter)
        if teams.exists():
            groups[group_letter] = teams

    context = {
        'groups': groups,
    }
    return render(request, 'tournament/standings.html', context)


def top_scorers(request):
    """Top scorers page"""
    # Get all players who have scored, count their goals
    players = Player.objects.annotate(
        goals_scored=Count('goals')
    ).filter(goals_scored__gt=0).order_by('-goals_scored', 'name')

    context = {
        'players': players,
    }
    return render(request, 'tournament/top_scorers.html', context)


def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    goals = match.goals.select_related('player', 'team')

    context = {
        'match': match,
        'goals': goals,
    }
    return render(request, 'tournament/match_detail.html', context)


# Custom Admin Views
@login_required
def admin_dashboard(request):
    """Custom admin dashboard"""
    teams_count = Team.objects.count()
    players_count = Player.objects.count()
    matches_count = Match.objects.count()

    context = {
        'teams_count': teams_count,
        'players_count': players_count,
        'matches_count': matches_count,
    }
    return render(request, 'tournament/admin_dashboard.html', context)


@login_required
def admin_teams(request):
    """Manage teams"""
    teams = Team.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        group = request.POST.get('group')

        Team.objects.create(name=name, group=group)
        messages.success(request, f'Team "{name}" added successfully!')
        return redirect('tournament:admin_teams')

    context = {'teams': teams}
    return render(request, 'tournament/admin_teams.html', context)


@login_required
def admin_players(request):
    """Manage players"""
    players = Player.objects.all()
    teams = Team.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        team_id = request.POST.get('team')
        team = Team.objects.get(id=team_id)

        Player.objects.create(name=name, team=team)
        messages.success(request, f'Player "{name}" added successfully!')
        return redirect('tournament:admin_players')

    context = {'players': players, 'teams': teams}
    return render(request, 'tournament/admin_players.html', context)


@login_required
def admin_matches(request):
    """Manage matches"""
    matches = Match.objects.all()
    teams = Team.objects.all()

    if request.method == 'POST':
        home_team_id = request.POST.get('home_team')
        away_team_id = request.POST.get('away_team')
        stage = request.POST.get('stage')
        match_time = request.POST.get('match_time')
        match_order = request.POST.get('match_order')

        home_team = Team.objects.get(id=home_team_id)
        away_team = Team.objects.get(id=away_team_id)

        Match.objects.create(
            home_team=home_team,
            away_team=away_team,
            stage=stage,
            match_time=match_time if match_time else None,
            match_order=match_order
        )
        messages.success(request, 'Match created successfully!')
        return redirect('tournament:admin_matches')

    context = {'matches': matches, 'teams': teams}
    return render(request, 'tournament/admin_matches.html', context)


@login_required
def admin_match_result(request, match_id):
    """Enter match result and goals"""
    match = get_object_or_404(Match, id=match_id)
    home_players = Player.objects.filter(team=match.home_team)
    away_players = Player.objects.filter(team=match.away_team)

    if request.method == 'POST':
        # Update match score
        match.home_score = int(request.POST.get('home_score', 0))
        match.away_score = int(request.POST.get('away_score', 0))
        match.status = 'finished'
        match.save()

        # Clear existing goals
        match.goals.all().delete()

        # Add home team goals
        home_goal_count = int(match.home_score)
        for i in range(home_goal_count):
            player_id = request.POST.get(f'home_goal_{i}')
            if player_id:
                player = Player.objects.get(id=player_id)
                Goal.objects.create(match=match, player=player, team=match.home_team)

        # Add away team goals
        away_goal_count = int(match.away_score)
        for i in range(away_goal_count):
            player_id = request.POST.get(f'away_goal_{i}')
            if player_id:
                player = Player.objects.get(id=player_id)
                Goal.objects.create(match=match, player=player, team=match.away_team)

        # IMPORTANT: Update team statistics!
        match.update_team_stats()

        messages.success(request, 'Match result saved and standings updated!')
        return redirect('tournament:admin_matches')

    context = {
        'match': match,
        'home_players': home_players,
        'away_players': away_players,
    }
    return render(request, 'tournament/admin_match_result.html', context)
