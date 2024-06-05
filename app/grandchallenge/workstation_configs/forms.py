from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django.forms import ModelForm
from django_select2.forms import Select2MultipleWidget

from grandchallenge.core.forms import SaveFormInitMixin
from grandchallenge.core.widgets import ColorEditorWidget, JSONEditorWidget
from grandchallenge.workstation_configs.models import (
    KEY_BINDINGS_SCHEMA,
    OVERLAY_SEGMENTS_SCHEMA,
    WorkstationConfig,
)

GENERAL_FIELDS = (
    "title",
    "description",
    "image_context",
    "window_presets",
    "default_window_preset",
    "default_slab_thickness_mm",
    "default_slab_render_method",
    "default_orientation",
    "default_image_interpolation",
    "default_limit_view_area_to_image_volume",
    "default_overlay_alpha",
    "ghosting_slice_depth",
    "overlay_luts",
    "default_overlay_lut",
    "default_overlay_interpolation",
    "overlay_segments",
    "key_bindings",
    "default_zoom_scale",
    "default_brush_size",
    "default_annotation_color",
    "default_annotation_line_width",
    "auto_jump_center_of_gravity",
    "point_bounding_box_size_mm",
)
PLUGIN_FIELDS = (
    "show_image_info_plugin",
    "show_display_plugin",
    "show_image_switcher_plugin",
    "show_algorithm_output_plugin",
    "show_overlay_plugin",
    "show_annotation_statistics_plugin",
    "show_swivel_tool",
    "show_invert_tool",
    "show_flip_tool",
    "show_window_level_tool",
    "show_reset_tool",
    "show_overlay_selection_tool",
    "show_lut_selection_tool",
    "show_annotation_counter_tool",
    "enable_contrast_enhancement",
)
LINKED_FIELDS = (
    "link_images",
    "link_panning",
    "link_zooming",
    "link_slicing",
    "link_orienting",
    "link_windowing",
    "link_inverting",
    "link_flipping",
)


class WorkstationConfigForm(SaveFormInitMixin, ModelForm):
    def __init__(self, *args, read_only=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Fieldset("", *GENERAL_FIELDS),
            Fieldset(
                "Plugins and Tools",
                *PLUGIN_FIELDS,
                css_class="border rounded px-2 my-4",
            ),
            Fieldset(
                "Linking Configuration",
                *PLUGIN_FIELDS,
                css_class="border rounded px-2 my-4",
            ),
        )

        if read_only:
            for field in self.fields:
                self.fields[field].disabled = True
        else:
            self.helper.layout.append(Submit("save", "Save"))

    class Meta:
        model = WorkstationConfig
        fields = (
            *GENERAL_FIELDS,
            *PLUGIN_FIELDS,
            *LINKED_FIELDS,
        )

        widgets = {
            "overlay_segments": JSONEditorWidget(
                schema=OVERLAY_SEGMENTS_SCHEMA
            ),
            "key_bindings": JSONEditorWidget(schema=KEY_BINDINGS_SCHEMA),
            "default_annotation_color": ColorEditorWidget(format="hex"),
            "window_presets": Select2MultipleWidget,
            "overlay_luts": Select2MultipleWidget,
        }
        help_texts = {
            "overlay_segments": (
                model._meta.get_field("overlay_segments").help_text
                + ". If an categorical overlay is shown, it is possible to show toggles "
                "to change the visibility of the different overlay categories. To do "
                "so, configure the categories that should be displayed. Data from the"
                " algorithm's output.json can be added as an extra label to each "
                "toggle using jinja templating. "
                'For example: [{ "voxel_value": 0, "name": "Level 0", "visible": '
                'false, "metric_template": "{{metrics.volumes[0]}} mm³"},]'
            ),
            "key_bindings": model._meta.get_field("key_bindings").help_text
            + ". A copy and paste JSON can be obtained from the viewer.",
        }
