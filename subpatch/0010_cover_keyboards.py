from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: run the decrypt and WiFi keyboards the full screen width"
        self.target_file = "bootable/recovery/aeraui/scenes/decrypt_scene.cpp"

        self.CHANGES = [
            (
                r"""
  state->keyboard = lv_keyboard_create(panel);
  phone_keyboard::Apply(state->keyboard);
  // Keyboard widgets default to BOTTOM_MID. Coordinates below are relative
  // to the panel's top left, just like the credential field and action buttons.
  lv_obj_set_align(state->keyboard, LV_ALIGN_TOP_LEFT);
  lv_obj_set_pos(state->keyboard, 36, 720);
  lv_obj_set_size(state->keyboard, 1112, pin ? 1010 : 820);
""",
                r"""
  // Docked at the bottom of the screen and as wide as it, so the keys come out
  // phone-sized where the 1440-wide layout is scaled down for a narrower panel.
  // The panel is narrower than the screen, so the keyboard sits on the screen
  // itself and enters with the panel. Its OK key submits, as Unlock does.
  state->keyboard = lv_keyboard_create(lv_obj_get_parent(panel));
  phone_keyboard::Apply(state->keyboard);
  lv_obj_set_size(state->keyboard, 1440, 820);
  lv_obj_align(state->keyboard, LV_ALIGN_BOTTOM_MID, 0, -64);
  AnimateEnter(state->keyboard, 70, 28);
  lv_obj_add_event_cb(state->keyboard, [](lv_event_t *event) {
    SubmitDecrypt(static_cast<DecryptState *>(lv_event_get_user_data(event)));
  }, LV_EVENT_READY, state);
"""
            ),
            (
                r"""
  lv_obj_align(hint, LV_ALIGN_BOTTOM_MID, 0, pin ? -340 : -70);

  AnimateEnter(emblem, 0, 16);
""",
                r"""
  lv_obj_align(hint, LV_ALIGN_BOTTOM_MID, 0, pin ? -340 : -70);
  // A password's keyboard takes the bottom of the screen, so Unlock and Skip
  // move up under the credential field, with the hint beneath them.
  if (credential_type != 2 && !pin) {
    lv_obj_set_y(state->submit, 670);
    lv_obj_set_y(skip, 832);
    lv_obj_align(hint, LV_ALIGN_TOP_MID, 0,
                 lv_obj_get_style_y(panel, LV_PART_MAIN) + 988);
  }

  AnimateEnter(emblem, 0, 16);
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES),
            # The WiFi password sheet goes full width so its keyboard can too.
            ("bootable/recovery/aeraui/scenes/wifi_scene.cpp", [
                (
                    r"""
  lv_obj_set_size(sheet, 1312, 1260);
  lv_obj_align(sheet, LV_ALIGN_BOTTOM_MID, 0, -64);
  lv_obj_set_style_pad_all(sheet, 48, 0);
  auto *title = Label(sheet, network.ssid.c_str(), &lv_font_montserrat_48, kText);
  lv_obj_set_width(title, 1180);
""",
                    r"""
  lv_obj_set_size(sheet, 1440, 1260);
  lv_obj_align(sheet, LV_ALIGN_BOTTOM_MID, 0, -64);
  lv_obj_set_style_pad_all(sheet, 48, 0);
  auto *title = Label(sheet, network.ssid.c_str(), &lv_font_montserrat_48, kText);
  lv_obj_set_width(title, 1300);
"""
                ),
                (
                    r"""
  lv_obj_set_pos(input, 0, 130);
  lv_obj_set_size(input, 1216, 126);
""",
                    r"""
  lv_obj_set_pos(input, 0, 130);
  lv_obj_set_size(input, 1344, 126);
"""
                ),
                (
                    r"""
  lv_obj_set_pos(keyboard, 0, 286);
  lv_obj_set_size(keyboard, 1216, 650);
""",
                    r"""
  // -48 takes it over the sheet's padding, out to the sheet's edges.
  lv_obj_set_pos(keyboard, -48, 286);
  lv_obj_set_size(keyboard, 1440, 650);
"""
                ),
                (
                    r"""
  lv_obj_set_pos(cancel, 0, 996);
  lv_obj_set_size(cancel, 580, 116);
""",
                    r"""
  lv_obj_set_pos(cancel, 0, 996);
  lv_obj_set_size(cancel, 640, 116);
"""
                ),
                (
                    r"""
  lv_obj_set_pos(connect, 636, 996);
  lv_obj_set_size(connect, 580, 116);
""",
                    r"""
  lv_obj_set_pos(connect, 704, 996);
  lv_obj_set_size(connect, 640, 116);
"""
                ),
            ]),
        ]

    # BaseSubPatch handles one file; this change spans two.
    def _each(self, step):
        for self.target_file, self.CHANGES in self.FILES:
            step()
        self.target_file, self.CHANGES = self.FILES[0]

    def check(self):
        self._each(super().check)

    def mod(self):
        self._each(super().mod)

    def list_changes(self):
        self._each(super().list_changes)
