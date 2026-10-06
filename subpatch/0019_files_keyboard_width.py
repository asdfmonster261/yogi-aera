from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: run the file manager keyboards the full screen width"
        self.target_file = "bootable/recovery/aeraui/scenes/home_scene.cpp"

        self.CHANGES = [
            # The name dialog (new folder, rename).
            (
                r"""
  const int width = landscape ? std::min(1900, screen_width - 128)
                              : std::min(1312, screen_width - 80);
  const int height = landscape ? 1250 : 1450;
""",
                r"""
  // Portrait runs the sheet, and with it the keyboard, the full screen width.
  const int width = landscape ? std::min(1900, screen_width - 128)
                              : screen_width;
  const int height = landscape ? 1250 : 1450;
"""
            ),
            (
                r"""
  lv_obj_align(keyboard, LV_ALIGN_TOP_LEFT, margin, keyboard_y);
  lv_obj_set_size(keyboard, width - 2 * margin, keyboard_height);
""",
                r"""
  lv_obj_align(keyboard, LV_ALIGN_TOP_LEFT, landscape ? margin : 0, keyboard_y);
  lv_obj_set_size(keyboard, landscape ? width - 2 * margin : width,
                  keyboard_height);
"""
            ),
            # The text editor, portrait.
            (
                r"""
    lv_obj_align(keyboard, LV_ALIGN_TOP_LEFT, margin, keyboard_y);
    lv_obj_set_size(keyboard, screen_width - 2 * margin, keyboard_height);
""",
                r"""
    // The keyboard runs the full screen width; the rest keeps its margins.
    lv_obj_align(keyboard, LV_ALIGN_TOP_LEFT, 0, keyboard_y);
    lv_obj_set_size(keyboard, screen_width, keyboard_height);
"""
            ),
        ]
