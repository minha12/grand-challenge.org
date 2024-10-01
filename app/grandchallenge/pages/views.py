import re
from datetime import datetime

import pypandoc
from bs4 import BeautifulSoup
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import Http404
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_countries import countries
from guardian.mixins import LoginRequiredMixin

from grandchallenge.challenges.views import ActiveChallengeRequiredMixin
from grandchallenge.charts.specs import stacked_bar, world_map
from grandchallenge.core.guardian import ObjectPermissionRequiredMixin
from grandchallenge.evaluation.models import Evaluation, Submission
from grandchallenge.pages.forms import PageCreateForm, PageUpdateForm
from grandchallenge.pages.models import Page
from grandchallenge.subdomains.utils import reverse, reverse_lazy


class ChallengeFilteredQuerysetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(challenge=self.request.challenge)


class ChallengeFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"challenge": self.request.challenge})
        return kwargs


class PageCreate(
    LoginRequiredMixin,
    ObjectPermissionRequiredMixin,
    ActiveChallengeRequiredMixin,
    CreateView,
):
    model = Page
    form_class = PageCreateForm
    permission_required = "change_challenge"
    raise_exception = True
    login_url = reverse_lazy("account_login")

    def get_permission_object(self):
        return self.request.challenge

    def form_valid(self, form):
        form.instance.challenge = self.request.challenge
        return super().form_valid(form)


class PageList(
    LoginRequiredMixin,
    ObjectPermissionRequiredMixin,
    ChallengeFilteredQuerysetMixin,
    ListView,
):
    model = Page
    permission_required = "change_challenge"
    raise_exception = True
    login_url = reverse_lazy("account_login")

    def get_permission_object(self):
        return self.request.challenge


class PageDetail(
    UserPassesTestMixin, ChallengeFilteredQuerysetMixin, DetailView
):
    model = Page
    raise_exception = True
    login_url = reverse_lazy("account_login")

    def test_func(self):
        user = self.request.user
        page = self.get_object()
        return page.can_be_viewed_by(user=user)


def html2md(*, html):
    soup = BeautifulSoup(html, "html.parser")

    for span in soup.find_all("span"):
        span.unwrap()

    # Remove empty divs, but allow alerts
    for div in soup.find_all("div"):
        is_alert = div.get("class") and "alert" in div["class"]

        if is_alert:
            div["markdown"] = "1"
        else:
            div.unwrap()

    # Remove empty headers
    for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if not header.get_text(strip=True) and not header.find("img"):
            header.decompose()

    markdown = pypandoc.convert_text(
        source=str(soup),
        format="html",
        to="gfm",
        sandbox=True,
    )

    # Replace image tags that span multiple lines
    markdown = re.sub(
        r"<img\s+([^>]+)>",
        lambda match: "<img " + match.group(1).replace("\n", " ") + ">",
        markdown,
    )
    markdown = re.sub(
        r"<a\s+([^>]+)>",
        lambda match: "<a " + match.group(1).replace("\n", " ") + ">",
        markdown,
    )

    # Empty headers
    markdown = re.sub(r"^\s*#+\s*$\n?", "", markdown, flags=re.MULTILINE)

    # Nested list correction
    markdown = re.sub(r"^\s*- - ", "  - ", markdown, flags=re.MULTILINE)

    return markdown


class ChallengeHome(PageDetail):
    def get_object(self, queryset=None):
        page = self.request.challenge.page_set.first()

        if page is None:
            raise Http404("No pages found for this challenge")

        return page


class PageUpdate(
    LoginRequiredMixin,
    ObjectPermissionRequiredMixin,
    ChallengeFilteredQuerysetMixin,
    UpdateView,
):
    model = Page
    form_class = PageUpdateForm
    permission_required = "change_challenge"
    raise_exception = True
    login_url = reverse_lazy("account_login")

    def get_permission_object(self):
        return self.request.challenge

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.move(form.cleaned_data["move"])
        return response


class PageDelete(
    LoginRequiredMixin,
    ObjectPermissionRequiredMixin,
    ChallengeFilteredQuerysetMixin,
    SuccessMessageMixin,
    DeleteView,
):
    model = Page
    success_message = "Page was successfully deleted"
    permission_required = "change_challenge"
    raise_exception = True
    login_url = reverse_lazy("account_login")

    def get_permission_object(self):
        return self.request.challenge

    def get_success_url(self):
        return reverse(
            "pages:list",
            kwargs={"challenge_short_name": self.request.challenge.short_name},
        )


class ChallengeStatistics(TemplateView):
    template_name = "pages/challenge_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        participants = (
            self.request.challenge.get_participants().select_related(
                "user_profile", "verification"
            )
        )

        participants_countries = (
            participants.exclude(user_profile__country="")
            .values("user_profile__country")
            .annotate(country_count=Count("user_profile__country"))
            .order_by("-country_count")
            .values_list("user_profile__country", "country_count")
        )

        public_phases = self.request.challenge.phase_set.filter(public=True)

        submissions = (
            Submission.objects.filter(phase__in=public_phases)
            .values("phase__pk", "created__year", "created__month")
            .annotate(object_count=Count("phase__slug"))
            .order_by("created__year", "created__month", "phase__pk")
        )

        context.update(
            {
                "participants": world_map(
                    values=[
                        {
                            "id": countries.numeric(c[0], padded=True),
                            "participants": c[1],
                        }
                        for c in participants_countries
                    ]
                ),
                "participants_total": participants.count(),
                "submissions": stacked_bar(
                    values=[
                        {
                            "Month": datetime(
                                datum["created__year"],
                                datum["created__month"],
                                1,
                            ).isoformat(),
                            "New Submissions": datum["object_count"],
                            "Phase": datum["phase__pk"],
                        }
                        for datum in submissions
                    ],
                    lookup="New Submissions",
                    title="New Submissions per Month",
                    facet="Phase",
                    domain=[
                        (phase.pk, phase.title) for phase in public_phases
                    ],
                ),
                "annotated_phases": self.request.challenge.phase_set.annotate(
                    num_submissions=Count("submission", distinct=True),
                    num_successful_submissions=Count(
                        "submission",
                        filter=Q(
                            submission__evaluation__status=Evaluation.SUCCESS
                        ),
                        distinct=True,
                    ),
                    num_creators=Count("submission__creator", distinct=True),
                    num_archive_items=Count("archive__items", distinct=True),
                ),
            }
        )

        return context
