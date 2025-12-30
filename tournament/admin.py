from django.contrib import admin

from .models import Goal, Match, Player, Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'played', 'won', 'drawn', 'lost', 'goals_for', 'goals_against', 'goal_difference', 'points']
    list_filter = ['group']
    search_fields = ['name']
    readonly_fields = ['played', 'won', 'drawn', 'lost', 'goals_for', 'goals_against', 'points']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'goal_count']
    list_filter = ['team']
    search_fields = ['name']


class GoalInline(admin.TabularInline):
    model = Goal
    extra = 1
    autocomplete_fields = ['player']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'match_time', 'stage', 'home_score', 'away_score', 'status', 'group']  # Added match_time
    list_filter = ['status', 'stage', 'group']
    search_fields = ['home_team__name', 'away_team__name']
    inlines = [GoalInline]

    fieldsets = (
        ('Match Details', {
            'fields': ('home_team', 'away_team', 'stage', 'match_time', 'match_order')  # Added match_time
        }),
        ('Result', {
            'fields': ('status', 'home_score', 'away_score')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == 'finished':
            obj.update_team_stats()


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['player', 'team', 'match']
    list_filter = ['team', 'match']
    search_fields = ['player__name']
    autocomplete_fields = ['player']
