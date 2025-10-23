from django.contrib import admin

from .models import RunnerAchievement, UserProfile, UserRaceHistory


class RunnerAchievementInline(admin.TabularInline):
    model = RunnerAchievement
    extra = 0


class UserRaceHistoryInline(admin.TabularInline):
    model = UserRaceHistory
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "city", "country", "favorite_distance")
    search_fields = ("user__username", "display_name", "city", "country")
    list_filter = ("favorite_distance", "country")
    inlines = [RunnerAchievementInline, UserRaceHistoryInline]


@admin.register(UserRaceHistory)
class UserRaceHistoryAdmin(admin.ModelAdmin):
    list_display = ("profile", "event", "status", "registration_date", "finish_time")
    list_filter = ("status", "event")
    search_fields = ("profile__user__username", "event__title", "category", "bib_number")


@admin.register(RunnerAchievement)
class RunnerAchievementAdmin(admin.ModelAdmin):
    list_display = ("profile", "title", "achieved_on")
    list_filter = ("achieved_on",)
    search_fields = ("profile__user__username", "title")
