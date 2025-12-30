from django.db.models import Count
from django.shortcuts import get_object_or_404, render

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
    players = Player.objects.annotate(
        goals=Count('goals')
    ).filter(goals__gt=0).order_by('-goals', 'name')

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
