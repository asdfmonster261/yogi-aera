from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: take the layout height from the panel"
        self.target_file = "bootable/recovery/aeraui/platform/aera_ui_host.cpp"

        self.CHANGES = [
            (
                r"""
#include <aeraui/backend.hpp>
#include <aeraui/runner.hpp>
""",
                r"""
#include <aeraui/backend.hpp>
#include <aeraui/display_transform.hpp>
#include <aeraui/runner.hpp>
"""
            ),
            (
                r"""
constexpr aeraui::DisplayMetrics kDisplayMetrics{
    false, 3168, 165, AERA_STATUS_INDENT_LEFT, AERA_STATUS_INDENT_RIGHT};
#endif

}  // namespace
""",
                r"""
constexpr aeraui::DisplayMetrics kDisplayMetrics{
    false, 3168, 165, AERA_STATUS_INDENT_LEFT, AERA_STATUS_INDENT_RIGHT};
#endif

// The adaptive layout is 1440 logical pixels wide and is stretched over the panel along
// each axis, so its height has to follow the panel's own aspect ratio. Otherwise one
// image squashes the layout on any phone whose panel differs from the one AERA_SCREEN_H
// was set for. The build-time height stays for a panel that is not portrait.
aeraui::DisplayMetrics PanelMetrics() {
  aeraui::DisplayMetrics metrics = kDisplayMetrics;
  const int width = gr_fb_width();
  const int height = gr_fb_height();
  if (metrics.adaptive_resolution && width > 0 && height > width)
    metrics.logical_height = static_cast<int32_t>(
        static_cast<int64_t>(aeraui::DisplayTransform::kDesignWidth) * height / width);
  return metrics;
}

}  // namespace
"""
            ),
            (
                r"""
  if (!fastboot && !soft_switch) {
    aeraui::StartAeraUiEarly(kDisplayMetrics);
""",
                r"""
  if (!fastboot && !soft_switch) {
    const auto metrics = PanelMetrics();
    gui_print("I:AERA layout 1440x%d on a %dx%d panel.\n", metrics.logical_height,
              gr_fb_width(), gr_fb_height());
    aeraui::StartAeraUiEarly(metrics);
"""
            ),
            (
                r"""
      ? aeraui::RunAeraUiFastboot(kDisplayMetrics)
      : resume ? aeraui::RunAeraUiResume(kDisplayMetrics)
               : aeraui::RunAeraUi(kDisplayMetrics);
""",
                r"""
      ? aeraui::RunAeraUiFastboot(PanelMetrics())
      : resume ? aeraui::RunAeraUiResume(PanelMetrics())
               : aeraui::RunAeraUi(PanelMetrics());
"""
            ),
        ]
