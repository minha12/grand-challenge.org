from django.urls import path

from grandchallenge.evaluation.views import (
    CombinedLeaderboardCreate,
    CombinedLeaderboardDelete,
    CombinedLeaderboardDetail,
    CombinedLeaderboardUpdate,
    ConfigureAlgorithmPhasesView,
    EvaluationAdminList,
    EvaluationCreate,
    EvaluationDetail,
    EvaluationGroundTruthCreate,
    EvaluationGroundTruthDetail,
    EvaluationGroundTruthList,
    EvaluationGroundTruthUpdate,
    EvaluationGroundTruthVersionManagement,
    EvaluationList,
    EvaluationStatusBadgeDetail,
    EvaluationUpdate,
    LeaderboardDetail,
    LeaderboardRedirect,
    MethodCreate,
    MethodDetail,
    MethodList,
    MethodUpdate,
    PhaseAlgorithmCreate,
    PhaseArchiveInfo,
    PhaseCreate,
    PhaseUpdate,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionList,
)

app_name = "evaluation"

urlpatterns = [
    path("<uuid:pk>/", EvaluationDetail.as_view(), name="detail"),
    path(
        "<uuid:pk>/status-badge/",
        EvaluationStatusBadgeDetail.as_view(),
        name="evaluation-status-badge-detail",
    ),
    # UUID should be matched before slugs
    path("<uuid:pk>/update/", EvaluationUpdate.as_view(), name="update"),
    path("phase/create/", PhaseCreate.as_view(), name="phase-create"),
    path(
        "configure-algorithm-phases/",
        ConfigureAlgorithmPhasesView.as_view(),
        name="configure-algorithm-phases",
    ),
    path("submissions/", SubmissionList.as_view(), name="submission-list"),
    path(
        "combined-leaderboards/create/",
        CombinedLeaderboardCreate.as_view(),
        name="combined-leaderboard-create",
    ),
    path(
        "combined-leaderboards/<slug>/",
        CombinedLeaderboardDetail.as_view(),
        name="combined-leaderboard-detail",
    ),
    path(
        "combined-leaderboards/<slug>/update/",
        CombinedLeaderboardUpdate.as_view(),
        name="combined-leaderboard-update",
    ),
    path(
        "combined-leaderboards/<slug>/delete/",
        CombinedLeaderboardDelete.as_view(),
        name="combined-leaderboard-delete",
    ),
    path("<slug>/", EvaluationList.as_view(), name="list"),
    path(
        "<slug>/admin/",
        EvaluationAdminList.as_view(),
        name="evaluation-admin-list",
    ),
    path(
        "<slug>/algorithms/create/",
        PhaseAlgorithmCreate.as_view(),
        name="phase-algorithm-create",
    ),
    path(
        "<slug>/linked-archive/",
        PhaseArchiveInfo.as_view(),
        name="phase-archive-info",
    ),
    path(
        "<slug>/ground-truths/",
        EvaluationGroundTruthList.as_view(),
        name="ground-truth-list",
    ),
    path(
        "<slug>/ground-truths/activate/",
        EvaluationGroundTruthVersionManagement.as_view(activate=True),
        name="ground-truth-activate",
    ),
    path(
        "<slug>/ground-truths/create/",
        EvaluationGroundTruthCreate.as_view(),
        name="ground-truth-create",
    ),
    path(
        "<slug>/ground-truths/deactivate/",
        EvaluationGroundTruthVersionManagement.as_view(activate=False),
        name="ground-truth-deactivate",
    ),
    path(
        "<slug>/ground-truths/<uuid:pk>/",
        EvaluationGroundTruthDetail.as_view(),
        name="ground-truth-detail",
    ),
    path(
        "<slug>/ground-truths/<uuid:pk>/update/",
        EvaluationGroundTruthUpdate.as_view(),
        name="ground-truth-update",
    ),
    path(
        "<slug>/leaderboard/", LeaderboardDetail.as_view(), name="leaderboard"
    ),
    path("<slug>/methods/", MethodList.as_view(), name="method-list"),
    path(
        "<slug>/methods/create/", MethodCreate.as_view(), name="method-create"
    ),
    path(
        "<slug>/methods/<uuid:pk>/",
        MethodDetail.as_view(),
        name="method-detail",
    ),
    path(
        "<slug>/methods/<uuid:pk>/update/",
        MethodUpdate.as_view(),
        name="method-update",
    ),
    path(
        "<slug>/submissions/create/",
        SubmissionCreate.as_view(),
        name="submission-create",
    ),
    path(
        "<slug>/submissions/<uuid:pk>/",
        SubmissionDetail.as_view(),
        name="submission-detail",
    ),
    path(
        "<slug>/submissions/<uuid:pk>/evaluations/create/",
        EvaluationCreate.as_view(),
        name="evaluation-create",
    ),
    path("<slug>/update/", PhaseUpdate.as_view(), name="phase-update"),
    path("results/", LeaderboardRedirect.as_view()),
    path("leaderboard/", LeaderboardRedirect.as_view()),
]
