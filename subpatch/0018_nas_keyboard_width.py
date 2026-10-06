from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: run the NAS field keyboard the full screen width"
        self.target_file = "bootable/recovery/aeraui/scenes/nas_scene.cpp"

        self.CHANGES = [
            (
                r"""
  lv_obj_set_size(sheet, 1312, 1260);
  lv_obj_align(sheet, LV_ALIGN_BOTTOM_MID, 0, -64);
  lv_obj_set_style_pad_all(sheet, 48, 0);
  auto *title = Label(sheet, FieldTitle(field), &lv_font_montserrat_48, kText);
  lv_obj_set_width(title, 1180);
""",
                r"""
  lv_obj_set_size(sheet, 1440, 1260);
  lv_obj_align(sheet, LV_ALIGN_BOTTOM_MID, 0, -64);
  lv_obj_set_style_pad_all(sheet, 48, 0);
  auto *title = Label(sheet, FieldTitle(field), &lv_font_montserrat_48, kText);
  lv_obj_set_width(title, 1300);
"""
            ),
            (
                r"""
  lv_obj_set_pos(hint, 0, 76);
  lv_obj_set_width(hint, 1180);

  auto *input = TextArea(sheet);
  lv_obj_set_pos(input, 0, 150);
  lv_obj_set_size(input, 1216, 126);
""",
                r"""
  lv_obj_set_pos(hint, 0, 76);
  lv_obj_set_width(hint, 1300);

  auto *input = TextArea(sheet);
  lv_obj_set_pos(input, 0, 150);
  lv_obj_set_size(input, 1344, 126);
"""
            ),
            (
                r"""
  lv_obj_set_pos(keyboard, 0, 306);
  lv_obj_set_size(keyboard, 1216, 630);
""",
                r"""
  // -48 takes it over the sheet's padding, out to the sheet's edges.
  lv_obj_set_pos(keyboard, -48, 306);
  lv_obj_set_size(keyboard, 1440, 630);
"""
            ),
            (
                r"""
  lv_obj_set_pos(cancel, 0, 986);
  lv_obj_set_size(cancel, 580, 116);
""",
                r"""
  lv_obj_set_pos(cancel, 0, 986);
  lv_obj_set_size(cancel, 640, 116);
"""
            ),
            (
                r"""
  lv_obj_set_pos(save, 636, 986);
  lv_obj_set_size(save, 580, 116);
""",
                r"""
  lv_obj_set_pos(save, 704, 986);
  lv_obj_set_size(save, 640, 116);
"""
            ),
        ]
