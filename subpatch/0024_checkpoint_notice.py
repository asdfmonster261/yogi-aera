from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: warn when /data is in checkpoint mode"
        self.target_file = "bootable/recovery/aeraui/core/engine.cpp"

        self.CHANGES = [
            (
                r"""
    PollAutomaticUpdates();
    PollRecentsHold();
""",
                r"""
    PollAutomaticUpdates();
    PollCheckpointNotice();
    PollRecentsHold();
"""
            ),
            (
                r"""
  void ShowUpdateBanner(const std::string &version) {
    if (!initialized_ || suspended_) return;
""",
                r"""
  // Android commits a pending userdata checkpoint (an OTA's first boot, staged Play
  // system updates) only once it has booted fully. Until then vold mounts /data with
  // checkpoint=disable here too, and f2fs drops everything written in this session
  // at the next mount.
  void PollCheckpointNotice() {
    if (checkpoint_notice_done_ || !initialized_ || suspended_ || fastboot_mode_ ||
        decryption_active_ || operation_running_ ||
        current_scene_ != Action::kBackHome)
      return;
    const uint32_t now = MonotonicMilliseconds();
    if (now - last_checkpoint_poll_ < 2000) return;
    last_checkpoint_poll_ = now;
    FILE *mounts = fopen("/proc/mounts", "re");
    if (mounts == nullptr) return;
    bool mounted = false;
    bool checkpointing = false;
    char *line = nullptr;
    size_t size = 0;
    while (getline(&line, &size, mounts) > 0) {
      if (strstr(line, " /data ") == nullptr) continue;
      mounted = true;
      if (strstr(line, " /data f2fs ") != nullptr &&
          strstr(line, "checkpoint=disable") != nullptr)
        checkpointing = true;
    }
    free(line);
    fclose(mounts);
    if (!mounted) return;
    checkpoint_notice_done_ = true;
    if (!checkpointing) return;
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "/data is mounted with checkpoint=disable; changes made "
                        "here are dropped at the next mount");
    ShowCheckpointNotice();
  }

  void ShowCheckpointNotice() {
    if (notice_overlay_ != nullptr) lv_obj_delete(notice_overlay_);
    auto *panel = lv_obj_create(lv_layer_top());
    notice_overlay_ = panel;
    design::Panel(panel, 42, design::kMainSheet);
    lv_obj_set_size(panel, 1080, 176);
    lv_obj_align(panel, LV_ALIGN_TOP_MID, 0, -196);
    lv_obj_set_style_border_width(panel, 1, 0);
    lv_obj_set_style_border_color(panel, design::kAmber, 0);
    lv_obj_set_style_border_opa(panel, LV_OPA_60, 0);
    lv_obj_set_style_pad_all(panel, 0, 0);
    lv_obj_add_event_cb(panel, [](lv_event_t *event) {
      auto *self = static_cast<Impl *>(lv_event_get_user_data(event));
      auto *target = static_cast<lv_obj_t *>(lv_event_get_target(event));
      if (self != nullptr && self->notice_overlay_ == target)
        self->notice_overlay_ = nullptr;
    }, LV_EVENT_DELETE, this);
    auto *icon_plate = lv_obj_create(panel);
    design::Panel(icon_plate, 26, design::kAmberSoft);
    lv_obj_set_pos(icon_plate, 34, 30);
    lv_obj_set_size(icon_plate, 116, 116);
    auto *icon = design::Label(icon_plate, LV_SYMBOL_WARNING,
                               &lv_font_montserrat_40, design::kAmber);
    lv_obj_center(icon);
    auto *label = design::Label(panel, "Android has an update to finish",
                                &lv_font_montserrat_32, design::kText);
    lv_obj_set_pos(label, 184, 34);
    lv_obj_set_width(label, 840);
    lv_label_set_long_mode(label, LV_LABEL_LONG_DOT);
    auto *detail = design::Label(panel,
                                 "Changes made here are lost until Android boots once",
                                 &lv_font_montserrat_24, design::kMutedStrong);
    lv_obj_set_pos(detail, 184, 94);
    lv_obj_set_width(detail, 840);
    lv_label_set_long_mode(detail, LV_LABEL_LONG_DOT);
    widgets::OnClick(panel, [this] {
      if (notice_overlay_ != nullptr) {
        auto *notice = notice_overlay_;
        notice_overlay_ = nullptr;
        lv_obj_delete_async(notice);
      }
    });
    lv_anim_t enter;
    lv_anim_init(&enter);
    lv_anim_set_var(&enter, panel);
    lv_anim_set_values(&enter, lv_obj_get_y(panel), 190);
    lv_anim_set_duration(&enter, 240);
    lv_anim_set_path_cb(&enter, lv_anim_path_ease_out);
    lv_anim_set_exec_cb(&enter, [](void *target, int32_t value) {
      lv_obj_set_y(static_cast<lv_obj_t *>(target), value);
    });
    lv_anim_start(&enter);
    lv_obj_delete_delayed(panel, 10000);
  }

  void ShowUpdateBanner(const std::string &version) {
    if (!initialized_ || suspended_) return;
"""
            ),
            (
                r"""
  uint64_t update_banner_build_time_ = 0;
""",
                r"""
  uint64_t update_banner_build_time_ = 0;
  bool checkpoint_notice_done_ = false;
  uint32_t last_checkpoint_poll_ = 0;
"""
            ),
        ]
