from enum import Enum, auto
from functools import lru_cache, wraps
import time

from django.urls import reverse

from discord_webhook import DiscordWebhook
from discord_webhook.webhook import DiscordEmbed

from home.models import Professor, Review
from planetterp.config import WEBHOOK_URL_UPDATE

def semester_name(semester_number):
    seasons = {"01": "spring", "05": "summer", "08": "fall", "12": "winter"}
    season = seasons[semester_number[4:6]]

    year = int(semester_number[:4])

    # The winter semester starting in january 2021 is actually called 202012
    # internally, not 202112, so return the next year for winter to adjust.
    if season == "winter":
        year += 1

    return f"{season.capitalize()} {year}"

def semester_number(semester_name: str):
    seasons = {"spring": "01", "summer": "05", "fall": "08", "winter": "12"}
    season, year = semester_name.strip().split(' ')

    if season.lower() == "winter":
        year = int(year) + 1

    return f"{year}{seasons[season.lower()]}"

# This list must be kept in ascending order, as other parts of the codebase rely
# on the ordering.
RECENT_SEMESTERS = ["202008", "202012", "202101", "202105", "202108"]

class AdminAction(Enum):
    # Review actions
    REVIEW_VERIFY = "review_verify"
    REVIEW_HELP = "review_help"

    # Professor actions
    PROFESSOR_VERIFY = "professor_verify"
    PROFESSOR_EDIT = "professor_edit"
    PROFESSOR_MERGE = "professor_merge"
    PROFESSOR_DELETE = "professor_delete"
    PROFESSOR_SLUG = "professor_slug"

class ReviewsTableColumn(Enum):
    INFORMATION = auto()
    REVIEW = auto()
    STATUS = auto()
    ACTION = auto()

def slug_in_use_err(slug: str, name: str):
    return f"Slug '{slug}' is already in use by '{name}'. Please merge these professors together if they are the same person."

# adapted from https://stackoverflow.com/a/63674816
def ttl_cache(max_age, maxsize=128, typed=False):
    """
    An @lru_cache, but instead of caching indefinitely (or until purged from
    the cache, which in practice rarely happens), only caches for `max_age`
    seconds.

    That is, at the first function call with certain arguments, the result is
    cached. Then, when the funcion is called again with those arguments, if it
    has been more than `max_age` seconds since the first call, the result is
    recalculated and that value is cached. Otherwise, the cached value is
    returned.

    Warnings
    --------
    This function does not actually guarantee that the result will be cached for
    exactly `max_age` seconds. Rather it only guarantees that the result will be
    cached for at *most* `max_age` seconds. This is to simplify implementation.
    """
    def decorator(function):
        @lru_cache(maxsize=maxsize, typed=typed)
        def with_time_salt(*args, __time_salt, **kwargs):
            return function(*args, **kwargs)

        @wraps(function)
        def wrapper(*args, **kwargs):
            time_salt = time.time() // max_age
            return with_time_salt(*args, **kwargs, __time_salt=time_salt)

        return wrapper
    return decorator

def send_updates_webhook(request, *, include_professors=True, include_reviews=True):
    if not WEBHOOK_URL_UPDATE:
        return

    title = ""
    if include_professors:
        num_professors = Professor.objects.filter(status=Professor.Status.PENDING).count()
        title += f"{num_professors} unverified professor(s)"
    if include_professors and include_reviews:
        title += " and "
    if include_reviews:
        num_reviews = Review.objects.filter(status=Review.Status.PENDING).count()
        title += f"{num_reviews} unverified review(s)"

    webhook = DiscordWebhook(url=WEBHOOK_URL_UPDATE)
    embed = DiscordEmbed(title=title, description="\n",
        url=request.build_absolute_uri(reverse("admin")))

    webhook.add_embed(embed)
    webhook.execute()
