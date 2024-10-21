import logging
from datetime import datetime

from actstream.actions import follow, is_following
from actstream.models import Follow
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.signals import post_delete
from django.db.transaction import on_commit
from django.dispatch import receiver
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import get_valid_filename
from django_extensions.db.models import TitleSlugDescriptionModel
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm, remove_perm
from jinja2 import sandbox
from jinja2.exceptions import TemplateError
from stdimage import JPEGField

from grandchallenge.algorithms.tasks import update_algorithm_average_duration
from grandchallenge.anatomy.models import BodyStructure
from grandchallenge.charts.specs import stacked_bar
from grandchallenge.components.models import (  # noqa: F401
    CIVForObjectMixin,
    ComponentImage,
    ComponentInterface,
    ComponentInterfaceValue,
    ComponentJob,
    ComponentJobManager,
    GPUTypeChoices,
    ImportStatusChoices,
    Tarball,
)
from grandchallenge.core.guardian import get_objects_for_group
from grandchallenge.core.models import RequestBase, UUIDModel
from grandchallenge.core.storage import (
    get_logo_path,
    get_social_image_path,
    protected_s3_storage,
    public_s3_storage,
)
from grandchallenge.core.templatetags.bleach import md2html
from grandchallenge.core.utils.access_requests import (
    AccessRequestHandlingOptions,
    process_access_request,
)
from grandchallenge.core.validators import ExtensionValidator
from grandchallenge.credits.models import Credit
from grandchallenge.evaluation.utils import get
from grandchallenge.hanging_protocols.models import HangingProtocolMixin
from grandchallenge.modalities.models import ImagingModality
from grandchallenge.organizations.models import Organization
from grandchallenge.publications.models import Publication
from grandchallenge.reader_studies.models import DisplaySet
from grandchallenge.subdomains.utils import reverse
from grandchallenge.workstations.models import Workstation

logger = logging.getLogger(__name__)

JINJA_ENGINE = sandbox.ImmutableSandboxedEnvironment()


class Algorithm(UUIDModel, TitleSlugDescriptionModel, HangingProtocolMixin):
    editors_group = models.OneToOneField(
        Group,
        on_delete=models.PROTECT,
        editable=False,
        related_name="editors_of_algorithm",
    )
    users_group = models.OneToOneField(
        Group,
        on_delete=models.PROTECT,
        editable=False,
        related_name="users_of_algorithm",
    )
    logo = JPEGField(
        upload_to=get_logo_path,
        storage=public_s3_storage,
        variations=settings.STDIMAGE_LOGO_VARIATIONS,
    )
    social_image = JPEGField(
        upload_to=get_social_image_path,
        storage=public_s3_storage,
        blank=True,
        help_text="An image for this algorithm which is displayed when you post the link for this algorithm on social media. Should have a resolution of 640x320 px (1280x640 px for best display).",
        variations=settings.STDIMAGE_SOCIAL_VARIATIONS,
    )
    workstation = models.ForeignKey(
        "workstations.Workstation", on_delete=models.PROTECT
    )
    workstation_config = models.ForeignKey(
        "workstation_configs.WorkstationConfig",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    optional_hanging_protocols = models.ManyToManyField(
        "hanging_protocols.HangingProtocol",
        through="OptionalHangingProtocolAlgorithm",
        related_name="optional_for_algorithm",
        blank=True,
        help_text="Optional alternative hanging protocols for this algorithm",
    )
    public = models.BooleanField(
        default=False,
        help_text=(
            "Should this algorithm be visible to all users on the algorithm "
            "overview page? This does not grant all users permission to use "
            "this algorithm. Users will still need to be added to the "
            "algorithm users group in order to do that."
        ),
    )
    access_request_handling = models.CharField(
        max_length=25,
        choices=AccessRequestHandlingOptions.choices,
        default=AccessRequestHandlingOptions.MANUAL_REVIEW,
        help_text=("How would you like to handle access requests?"),
    )
    detail_page_markdown = models.TextField(blank=True)
    job_create_page_markdown = models.TextField(blank=True)
    additional_terms_markdown = models.TextField(
        blank=True,
        help_text=(
            "By using this algorithm, users agree to the site wide "
            "terms of service. If your algorithm has any additional "
            "terms of usage, define them here."
        ),
    )
    result_template = models.TextField(
        blank=True,
        default="<pre>{{ results|tojson(indent=2) }}</pre>",
        help_text=(
            "Define the jinja template to render the content of the "
            "results.json to html. For example, the following template will "
            "print out all the keys and values of the result.json. "
            "Use results to access the json root. "
            "{% for key, value in results.metrics.items() -%}"
            "{{ key }}  {{ value }}"
            "{% endfor %}"
        ),
    )
    inputs = models.ManyToManyField(
        to=ComponentInterface, related_name="algorithm_inputs", blank=False
    )
    outputs = models.ManyToManyField(
        to=ComponentInterface, related_name="algorithm_outputs", blank=False
    )
    publications = models.ManyToManyField(
        Publication,
        blank=True,
        help_text="The publications associated with this algorithm",
    )
    modalities = models.ManyToManyField(
        ImagingModality,
        blank=True,
        help_text="The imaging modalities supported by this algorithm",
    )
    structures = models.ManyToManyField(
        BodyStructure,
        blank=True,
        help_text="The structures supported by this algorithm",
    )
    organizations = models.ManyToManyField(
        Organization,
        blank=True,
        help_text="The organizations associated with this algorithm",
        related_name="algorithms",
    )
    minimum_credits_per_job = models.PositiveIntegerField(
        default=20,
        help_text=(
            "The minimum number of credits that are required for each execution of this algorithm. "
            "The actual number of credits required may be higher than this depending on the "
            "algorithms configuration."
        ),
        validators=[
            MinValueValidator(limit_value=20),
            MaxValueValidator(limit_value=1000),
        ],
    )
    time_limit = models.PositiveIntegerField(
        default=60 * 60,
        help_text="Time limit for inference jobs in seconds",
        validators=[
            MinValueValidator(
                limit_value=settings.COMPONENTS_MINIMUM_JOB_DURATION
            ),
            MaxValueValidator(
                limit_value=settings.COMPONENTS_MAXIMUM_JOB_DURATION
            ),
        ],
    )
    job_requires_gpu_type = models.CharField(
        max_length=4,
        blank=True,
        default=GPUTypeChoices.NO_GPU,
        choices=GPUTypeChoices.choices,
        help_text="What GPU to attach to this algorithms inference jobs",
    )
    job_requires_memory_gb = models.PositiveSmallIntegerField(
        default=8,
        help_text="How much memory to assign to this algorithms inference jobs",
    )
    average_duration = models.DurationField(
        null=True,
        default=None,
        editable=False,
        help_text="The average duration of successful jobs.",
    )
    repo_name = models.CharField(blank=True, max_length=512)
    recurse_submodules = models.BooleanField(
        default=False,
        help_text="Do a recursive git pull when a GitHub repo is linked to this algorithm.",
    )
    highlight = models.BooleanField(
        default=False,
        help_text="Should this algorithm be advertised on the home page?",
    )
    contact_email = models.EmailField(
        blank=True,
        help_text="This email will be listed as the contact email for the algorithm and will be visible to all users of Grand Challenge.",
    )
    display_editors = models.BooleanField(
        null=True,
        blank=True,
        help_text="Should the editors of this algorithm be listed on the information page?",
    )
    summary = models.TextField(
        blank=True,
        help_text="Briefly describe your algorithm and how it was developed.",
    )
    mechanism = models.TextField(
        blank=True,
        help_text="Provide a short technical description of your algorithm.",
    )
    validation_and_performance = models.TextField(
        blank=True,
        help_text="If you have performance metrics about your algorithm, you can report them here.",
    )
    uses_and_directions = models.TextField(
        blank=True,
        default="This algorithm was developed for research purposes only.",
        help_text="Describe what your algorithm can be used for, but also what it should not be used for.",
    )
    warnings = models.TextField(
        blank=True,
        help_text="Describe potential risks and inappropriate settings for using the algorithm.",
    )
    common_error_messages = models.TextField(
        blank=True,
        help_text="Describe common error messages a user might encounter when trying out your algorithm and provide solutions for them.",
    )
    editor_notes = models.TextField(
        blank=True,
        help_text="Add internal notes such as the deployed version number, code and data locations, etc. Only visible to editors.",
    )

    class Meta(UUIDModel.Meta, TitleSlugDescriptionModel.Meta):
        ordering = ("created",)
        permissions = [("execute_algorithm", "Can execute algorithm")]
        constraints = [
            models.UniqueConstraint(
                fields=["repo_name"],
                name="unique_repo_name",
                condition=~Q(repo_name=""),
            )
        ]

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse("algorithms:detail", kwargs={"slug": self.slug})

    @property
    def api_url(self) -> str:
        return reverse("api:algorithm-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        adding = self._state.adding

        if adding:
            self.create_groups()
            self.workstation_id = (
                self.workstation_id or self.default_workstation.pk
            )

        super().save(*args, **kwargs)

        self.assign_permissions()
        self.assign_workstation_permissions()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.filter(
            app_label=self._meta.app_label, model=self._meta.model_name
        ).get()
        Follow.objects.filter(object_id=self.pk, content_type=ct).delete()
        super().delete(*args, **kwargs)

    def create_groups(self):
        self.editors_group = Group.objects.create(
            name=f"{self._meta.app_label}_{self._meta.model_name}_{self.pk}_editors"
        )
        self.users_group = Group.objects.create(
            name=f"{self._meta.app_label}_{self._meta.model_name}_{self.pk}_users"
        )

    def assign_permissions(self):
        # Editors and users can view this algorithm
        assign_perm(f"view_{self._meta.model_name}", self.editors_group, self)
        assign_perm(f"view_{self._meta.model_name}", self.users_group, self)
        # Editors and users can execute this algorithm
        assign_perm(
            f"execute_{self._meta.model_name}", self.editors_group, self
        )
        assign_perm(f"execute_{self._meta.model_name}", self.users_group, self)
        # Editors can change this algorithm
        assign_perm(
            f"change_{self._meta.model_name}", self.editors_group, self
        )

        reg_and_anon = Group.objects.get(
            name=settings.REGISTERED_AND_ANON_USERS_GROUP_NAME
        )

        if self.public:
            assign_perm(f"view_{self._meta.model_name}", reg_and_anon, self)
        else:
            remove_perm(f"view_{self._meta.model_name}", reg_and_anon, self)

    def assign_workstation_permissions(self):
        """Allow the editors and users group to view the workstation."""
        perm = "workstations.view_workstation"

        for group in [self.users_group, self.editors_group]:
            workstations = get_objects_for_group(
                group=group,
                perms=perm,
            )

            if (
                self.workstation not in workstations
            ) or workstations.count() > 1:
                remove_perm(perm=perm, user_or_group=group, obj=workstations)
                assign_perm(
                    perm=perm, user_or_group=group, obj=self.workstation
                )

    @cached_property
    def active_image(self):
        """
        Returns
        -------
            The desired version for this algorithm or None
        """
        try:
            return (
                self.algorithm_container_images.executable_images()
                .filter(is_desired_version=True)
                .get()
            )
        except ObjectDoesNotExist:
            return None

    @cached_property
    def active_model(self):
        """
        Returns
        -------
            The desired model version for this algorithm or None
        """
        try:
            return self.algorithm_models.filter(is_desired_version=True).get()
        except ObjectDoesNotExist:
            return None

    @cached_property
    def credits_per_job(self):
        job = Job(
            algorithm_image=self.active_image,
            time_limit=self.time_limit,
            requires_gpu_type=self.job_requires_gpu_type,
            requires_memory_gb=self.job_requires_memory_gb,
        )
        job.init_credits_consumed()
        return job.credits_consumed

    @property
    def image_upload_in_progress(self):
        return self.algorithm_container_images.filter(
            import_status__in=(
                ImportStatusChoices.STARTED,
                ImportStatusChoices.QUEUED,
            )
        ).exists()

    @property
    def model_upload_in_progress(self):
        return self.algorithm_models.filter(
            import_status__in=(ImportStatusChoices.INITIALIZED,)
        ).exists()

    @cached_property
    def default_workstation(self):
        """
        Returns the default workstation, creating it if it does not already
        exist.
        """
        w, created = Workstation.objects.get_or_create(
            slug=settings.DEFAULT_WORKSTATION_SLUG
        )

        if created:
            w.title = settings.DEFAULT_WORKSTATION_SLUG
            w.save()

        return w

    def is_editor(self, user):
        return user.groups.filter(pk=self.editors_group.pk).exists()

    def add_editor(self, user):
        return user.groups.add(self.editors_group)

    def remove_editor(self, user):
        return user.groups.remove(self.editors_group)

    def is_user(self, user):
        return user.groups.filter(pk=self.users_group.pk).exists()

    def add_user(self, user):
        return user.groups.add(self.users_group)

    def remove_user(self, user):
        return user.groups.remove(self.users_group)

    @cached_property
    def user_statistics(self):
        return (
            get_user_model()
            .objects.select_related("verification", "user_profile")
            .annotate(
                job_count=Count(
                    "pk", filter=Q(job__algorithm_image__algorithm=self)
                )
            )
            .filter(job_count__gt=0)
            .order_by("-job_count")[:10]
        )

    @property
    def usage_chart_statuses(self):
        """What statuses should be included on the chart"""
        return [Job.SUCCESS, Job.CANCELLED, Job.FAILURE]

    @cached_property
    def usage_statistics(self):
        """The number of jobs for this algorithm faceted by month and status"""
        return (
            Job.objects.filter(
                algorithm_image__algorithm=self,
                status__in=self.usage_chart_statuses,
            )
            .values("status", "created__year", "created__month")
            .annotate(job_count=Count("status"))
            .order_by("created__year", "created__month", "status")
        )

    @cached_property
    def usage_chart(self):
        """Vega lite chart of the usage of this algorithm"""
        choices = dict(Job.status.field.choices)
        domain = {
            choice: choices[choice] for choice in self.usage_chart_statuses
        }

        return stacked_bar(
            values=[
                {
                    "Status": datum["status"],
                    "Month": datetime(
                        datum["created__year"], datum["created__month"], 1
                    ).isoformat(),
                    "Jobs Count": datum["job_count"],
                }
                for datum in self.usage_statistics
            ],
            lookup="Jobs Count",
            title="Algorithm Usage",
            facet="Status",
            domain=domain,
        )

    @cached_property
    def public_test_case(self):
        try:
            return self.active_image.job_set.filter(
                status=Job.SUCCESS,
                public=True,
                algorithm_model=self.active_model,
            ).exists()
        except AttributeError:
            return False

    def form_field_label(self):
        title = f"{self.title}"
        title += f" (Active image: {' - '.join(filter(None, [truncatechars(self.active_image_comment, 25), str(self.active_image_pk)]))})"
        if self.active_model_pk:
            title += f" (Active model: {' - '.join(filter(None, [truncatechars(self.active_model_comment, 25), str(self.active_model_pk)]))})"
        else:
            title += " (Active model: None)"
        return title


class AlgorithmUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Algorithm, on_delete=models.CASCADE)


class AlgorithmGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Algorithm, on_delete=models.CASCADE)


@receiver(post_delete, sender=Algorithm)
def delete_algorithm_groups_hook(*_, instance: Algorithm, using, **__):
    """
    Deletes the related groups.

    We use a signal rather than overriding delete() to catch usages of
    bulk_delete.
    """
    try:
        instance.editors_group.delete(using=using)
    except ObjectDoesNotExist:
        pass

    try:
        instance.users_group.delete(using=using)
    except ObjectDoesNotExist:
        pass


class AlgorithmImage(UUIDModel, ComponentImage):
    algorithm = models.ForeignKey(
        Algorithm,
        on_delete=models.PROTECT,
        related_name="algorithm_container_images",
    )

    class Meta(UUIDModel.Meta, ComponentImage.Meta):
        ordering = ("created", "creator")
        permissions = [
            ("download_algorithmimage", "Can download algorithm image")
        ]

    def get_absolute_url(self):
        return reverse(
            "algorithms:image-detail",
            kwargs={"slug": self.algorithm.slug, "pk": self.pk},
        )

    @property
    def api_url(self) -> str:
        return reverse("api:algorithms-image-detail", kwargs={"pk": self.pk})

    def get_remaining_complimentary_jobs(self, *, user):
        if self.algorithm.is_editor(user=user):
            return max(
                settings.ALGORITHM_IMAGES_COMPLIMENTARY_EDITOR_JOBS
                - Job.objects.filter(
                    algorithm_image=self, is_complimentary=True
                ).count(),
                0,
            )
        else:
            return 0

    def get_remaining_non_complimentary_jobs(self, *, user):
        user_credits = Credit.objects.get(user=user).credits
        spent_credits = Job.objects.credits_consumed_past_month(user=user)[
            "total"
        ]

        credits_left = user_credits - spent_credits

        return max(credits_left, 0) // max(self.algorithm.credits_per_job, 1)

    def get_remaining_jobs(self, *, user):
        return self.get_remaining_non_complimentary_jobs(
            user=user
        ) + self.get_remaining_complimentary_jobs(user=user)

    def save(self, *args, **kwargs):
        adding = self._state.adding

        super().save(*args, **kwargs)

        if adding:
            self.assign_permissions()

    def assign_permissions(self):
        # Editors and users can view this algorithm image
        assign_perm(
            f"view_{self._meta.model_name}", self.algorithm.editors_group, self
        )
        # Editors can change this algorithm image
        assign_perm(
            f"change_{self._meta.model_name}",
            self.algorithm.editors_group,
            self,
        )

    def get_peer_images(self):
        return AlgorithmImage.objects.filter(algorithm=self.algorithm)


class AlgorithmImageUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(
        AlgorithmImage, on_delete=models.CASCADE
    )


class AlgorithmImageGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        AlgorithmImage, on_delete=models.CASCADE
    )


class JobManager(ComponentJobManager):
    def create(
        self,
        *,
        input_civ_set=None,
        extra_viewer_groups=None,
        extra_logs_viewer_groups=None,
        **kwargs,
    ):
        obj = super().create(**kwargs)

        if input_civ_set is not None:
            obj.inputs.set(input_civ_set)

        if extra_viewer_groups is not None:
            obj.viewer_groups.add(*extra_viewer_groups)

        if extra_logs_viewer_groups is not None:
            for group in extra_logs_viewer_groups:
                assign_perm("algorithms.view_logs", group, obj)

        return obj

    @staticmethod
    def retrieve_existing_civs(*, civ_data):
        """
        Checks if there are existing CIVs for the provided data and returns those.

        Parameters
        ----------
        civ_data
            A list of CIVData objects.

        Returns
        -------
        A list of ComponentInterfaceValues

        """
        existing_civs = []
        for civ in civ_data:
            if (
                civ.user_upload
                or civ.upload_session
                or civ.user_upload_queryset
            ):
                # uploads will create new CIVs, so ignore these
                continue
            elif civ.image:
                try:
                    civs = ComponentInterfaceValue.objects.filter(
                        interface__slug=civ.interface_slug, image=civ.image
                    ).all()
                    existing_civs.extend(civs)
                except ObjectDoesNotExist:
                    continue
            elif civ.file_civ:
                existing_civs.append(civ.file_civ)
            else:
                # values can be of different types, including None and False
                try:
                    civs = ComponentInterfaceValue.objects.filter(
                        interface__slug=civ.interface_slug, value=civ.value
                    ).all()
                    existing_civs.extend(civs)
                except ObjectDoesNotExist:
                    continue

        return existing_civs

    def get_jobs_with_same_inputs(
        self, *, inputs, algorithm_image, algorithm_model
    ):
        existing_civs = self.retrieve_existing_civs(civ_data=inputs)
        unique_kwargs = {
            "algorithm_image": algorithm_image,
        }
        input_interface_count = algorithm_image.algorithm.inputs.count()

        if algorithm_model:
            unique_kwargs["algorithm_model"] = algorithm_model
        else:
            unique_kwargs["algorithm_model__isnull"] = True

        existing_jobs = (
            Job.objects.filter(**unique_kwargs)
            .annotate(
                inputs_match_count=Count(
                    "inputs", filter=Q(inputs__in=existing_civs)
                )
            )
            .filter(inputs_match_count=input_interface_count)
        )

        return existing_jobs

    def credits_consumed_past_month(self, user):
        return (
            self.filter(
                creator=user,
                created__gt=timezone.now() - relativedelta(months=1),
            )
            .exclude(is_complimentary=True)
            .aggregate(
                total=Sum("credits_consumed", default=0),
            )
        )


def algorithm_models_path(instance, filename):
    return (
        f"models/"
        f"{instance._meta.app_label.lower()}/"
        f"{instance._meta.model_name.lower()}/"
        f"{instance.pk}/"
        f"{get_valid_filename(filename)}"
    )


class AlgorithmModel(Tarball):
    algorithm = models.ForeignKey(
        Algorithm, on_delete=models.PROTECT, related_name="algorithm_models"
    )
    model = models.FileField(
        blank=True,
        upload_to=algorithm_models_path,
        validators=[ExtensionValidator(allowed_extensions=(".tar.gz",))],
        help_text=(
            ".tar.gz file of the algorithm model that will be extracted to /opt/ml/model/ during inference"
        ),
        storage=protected_s3_storage,
    )

    class Meta(Tarball.Meta):
        permissions = [
            ("download_algorithmmodel", "Can download algorithm model")
        ]

    @property
    def linked_file(self):
        return self.model

    def assign_permissions(self):
        # Editors can view this algorithm model
        assign_perm(
            f"view_{self._meta.model_name}", self.algorithm.editors_group, self
        )
        # Editors can change this algorithm model
        assign_perm(
            f"change_{self._meta.model_name}",
            self.algorithm.editors_group,
            self,
        )

    def get_peer_tarballs(self):
        return AlgorithmModel.objects.filter(algorithm=self.algorithm).exclude(
            pk=self.pk
        )

    def get_absolute_url(self):
        return reverse(
            "algorithms:model-detail",
            kwargs={"slug": self.algorithm.slug, "pk": self.pk},
        )


class AlgorithmModelUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(
        AlgorithmModel, on_delete=models.CASCADE
    )


class AlgorithmModelGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        AlgorithmModel, on_delete=models.CASCADE
    )


class Job(CIVForObjectMixin, ComponentJob):
    objects = JobManager.as_manager()

    algorithm_image = models.ForeignKey(
        AlgorithmImage, on_delete=models.PROTECT
    )
    algorithm_model = models.ForeignKey(
        AlgorithmModel, on_delete=models.PROTECT, null=True, blank=True
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    public = models.BooleanField(
        default=False,
        help_text=(
            "If True, allow anyone to download this result along "
            "with the input image. Otherwise, only the job creator "
            "will have permission to download and view "
            "this result."
        ),
    )
    comment = models.TextField(blank=True, default="")
    credits_consumed = models.PositiveSmallIntegerField(
        editable=False,
        help_text="The total credits consumed for this job",
    )
    is_complimentary = models.BooleanField(
        default=False,
        editable=False,
        help_text="If True, this job does not consume credits.",
    )

    viewer_groups = models.ManyToManyField(
        Group,
        help_text="Which groups should have permission to view this job?",
    )
    viewers = models.OneToOneField(
        Group,
        on_delete=models.PROTECT,
        related_name="viewers_of_algorithm_job",
    )

    class Meta(UUIDModel.Meta, ComponentJob.Meta):
        ordering = ("created",)
        permissions = [("view_logs", "Can view the jobs logs")]

    def __str__(self):
        return f"Job {self.pk}"

    @property
    def container(self):
        return self.algorithm_image

    @property
    def output_interfaces(self):
        return self.algorithm_image.algorithm.outputs

    @cached_property
    def inputs_complete(self):
        # check if all inputs are present and if they all have a value
        return {
            civ.interface for civ in self.inputs.all() if civ.has_value
        } == {*self.algorithm_image.algorithm.inputs.all()}

    @cached_property
    def rendered_result_text(self) -> str:
        try:
            results = get(
                [
                    o.value
                    for o in self.outputs.all()
                    if o.interface.slug == "results-json-file"
                ]
            )
        except ObjectDoesNotExist:
            return ""

        try:
            template_output = JINJA_ENGINE.from_string(
                self.algorithm_image.algorithm.result_template
            ).render(results=results)
        except (TemplateError, TypeError, ValueError):
            return "Jinja template is invalid"

        return md2html(template_output)

    def get_absolute_url(self):
        return reverse(
            "algorithms:job-detail",
            kwargs={
                "slug": self.algorithm_image.algorithm.slug,
                "pk": self.pk,
            },
        )

    @property
    def api_url(self) -> str:
        return reverse("api:algorithms-job-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        adding = self._state.adding

        if adding:
            self.init_viewers_group()
            self.init_is_complimentary()
            self.init_credits_consumed()

        super().save(*args, **kwargs)

        if adding:
            self.init_permissions()
            self.init_followers()

        self.update_viewer_groups_for_public()

        if self.has_changed("status") and self.status == self.SUCCESS:
            on_commit(
                update_algorithm_average_duration.signature(
                    kwargs={"algorithm_pk": self.algorithm_image.algorithm.pk}
                ).apply_async
            )

    def init_viewers_group(self):
        self.viewers = Group.objects.create(
            name=f"{self._meta.app_label}_{self._meta.model_name}_{self.pk}_viewers"
        )

    def init_is_complimentary(self):
        self.is_complimentary = bool(
            self.creator
            and self.algorithm_image.get_remaining_complimentary_jobs(
                user=self.creator
            )
            > 0
        )

    def init_credits_consumed(self):
        default_credits_per_month = Credit._meta.get_field(
            "credits"
        ).get_default()
        overall_min_credits_per_job = (
            default_credits_per_month
            / settings.ALGORITHMS_MAX_DEFAULT_JOBS_PER_MONTH
        )

        executor = self.get_executor(
            backend=settings.COMPONENTS_DEFAULT_BACKEND
        )

        maximum_cents_per_job = (
            (self.time_limit / 3600)
            * executor.usd_cents_per_hour
            * (1 + settings.COMPONENTS_TAX_RATE_PERCENT)
            * settings.COMPONENTS_USD_TO_EUR
        )

        credits_per_job = max(
            int(
                round(
                    maximum_cents_per_job
                    * default_credits_per_month
                    / settings.ALGORITHMS_USER_CENTS_PER_MONTH,
                    -1,
                )
            ),
            overall_min_credits_per_job,
        )

        self.credits_consumed = max(
            self.algorithm_image.algorithm.minimum_credits_per_job,
            credits_per_job,
        )

    def init_permissions(self):
        # By default, only the viewers can view this job
        self.viewer_groups.set([self.viewers])

        # If there is a creator they can view and change this job
        if self.creator:
            self.viewers.user_set.add(self.creator)
            assign_perm("change_job", self.creator, self)

    def init_followers(self):
        if self.creator:
            if not is_following(
                user=self.creator,
                obj=self.algorithm_image.algorithm,
                flag="job-active",
            ) and not is_following(
                user=self.creator,
                obj=self.algorithm_image.algorithm,
                flag="job-inactive",
            ):
                follow(
                    user=self.creator,
                    obj=self.algorithm_image.algorithm,
                    actor_only=False,
                    send_action=False,
                    flag="job-active",
                )

    def update_viewer_groups_for_public(self):
        g = Group.objects.get(
            name=settings.REGISTERED_AND_ANON_USERS_GROUP_NAME
        )

        if self.public:
            self.viewer_groups.add(g)
        else:
            self.viewer_groups.remove(g)

    def add_viewer(self, user):
        return user.groups.add(self.viewers)

    def remove_viewer(self, user):
        return user.groups.remove(self.viewers)

    def add_civ(self, *, civ):
        super().add_civ(civ=civ)
        return self.inputs.add(civ)

    def remove_civ(self, *, civ):
        super().remove_civ(civ=civ)
        return self.inputs.remove(civ)

    def get_civ_for_interface(self, interface):
        return self.inputs.get(interface=interface)

    def validate_inputs_and_execute(self, *, inputs):
        from grandchallenge.algorithms.tasks import (
            execute_algorithm_job_for_inputs,
        )

        linked_task = execute_algorithm_job_for_inputs.signature(
            kwargs={"job_pk": self.pk}, immutable=True
        )

        if not self.is_editable:
            raise RuntimeError(
                "Job is not editable. No CIVs can be added or removed from it."
            )
        else:
            for civ_data in inputs:
                self.create_civ(
                    civ_data=civ_data,
                    user=self.creator,
                    linked_task=linked_task,
                )

    @property
    def is_editable(self):
        # staying with display set and archive item terminology here
        # since this property is checked in create_civ()
        if self.status == self.VALIDATING_INPUTS:
            return True
        else:
            return False

    @property
    def base_object(self):
        return self.algorithm_image.algorithm

    @property
    def executor_kwargs(self):
        executor_kwargs = super().executor_kwargs
        if self.algorithm_model:
            executor_kwargs["algorithm_model"] = self.algorithm_model.model
        return executor_kwargs

    @cached_property
    def slug_to_output(self):
        outputs = {}

        for output in self.outputs.all():
            outputs[output.interface.slug] = output

        return outputs

    def get_or_create_display_set(self, *, reader_study):
        """Get or create a display set from this job for a reader study"""
        if self.status != self.SUCCESS:
            raise RuntimeError(
                "Display sets can only be created from successful jobs"
            )

        values = {*self.inputs.all(), *self.outputs.all()}

        try:
            display_set = (
                reader_study.display_sets.filter(values__in=values)
                .annotate(
                    values_match_count=Count(
                        "values",
                        filter=Q(values__in=values),
                    )
                )
                .filter(values_match_count=len(values))
                .get()
            )
        except ObjectDoesNotExist:
            display_set = DisplaySet.objects.create(reader_study=reader_study)
            display_set.values.set(values)

        return display_set


class JobUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Job, on_delete=models.CASCADE)


class JobGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Job, on_delete=models.CASCADE)


@receiver(post_delete, sender=Job)
def delete_job_groups_hook(*_, instance: Job, using, **__):
    """
    Deletes the related group.

    We use a signal rather than overriding delete() to catch usages of
    bulk_delete.
    """
    try:
        instance.viewers.delete(using=using)
    except ObjectDoesNotExist:
        pass


class AlgorithmPermissionRequest(RequestBase):
    """
    When a user wants to view an algorithm, editors have the option of
    reviewing each user before accepting or rejecting them. This class records
    the needed info for that.
    """

    algorithm = models.ForeignKey(
        Algorithm,
        help_text="To which algorithm has the user requested access?",
        on_delete=models.CASCADE,
    )
    rejection_text = models.TextField(
        blank=True,
        help_text=(
            "The text that will be sent to the user with the reason for their "
            "rejection."
        ),
    )

    @property
    def base_object(self):
        return self.algorithm

    @property
    def object_name(self):
        return self.base_object.title

    @property
    def add_method(self):
        return self.base_object.add_user

    @property
    def remove_method(self):
        return self.base_object.remove_user

    @property
    def permission_list_url(self):
        return reverse(
            "algorithms:permission-request-list",
            kwargs={"slug": self.base_object.slug},
        )

    def __str__(self):
        return f"{self.object_name} registration request by user {self.user.username}"

    def save(self, *args, **kwargs):
        adding = self._state.adding
        super().save(*args, **kwargs)
        if adding:
            process_access_request(request_object=self)

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.filter(
            app_label=self._meta.app_label, model=self._meta.model_name
        ).get()
        Follow.objects.filter(object_id=self.pk, content_type=ct).delete()
        super().delete(*args, **kwargs)

    class Meta(RequestBase.Meta):
        unique_together = (("algorithm", "user"),)


class OptionalHangingProtocolAlgorithm(models.Model):
    # Through table for optional hanging protocols
    # https://docs.djangoproject.com/en/4.2/topics/db/models/#intermediary-manytomany
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    hanging_protocol = models.ForeignKey(
        "hanging_protocols.HangingProtocol", on_delete=models.CASCADE
    )
