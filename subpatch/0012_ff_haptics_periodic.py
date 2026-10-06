from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "minuitwrp: drive force-feedback haptics that only play periodic effects"
        self.target_file = "bootable/recovery/minuitwrp/events.cpp"

        self.CHANGES = [
            (
                r"""
        int fallback_fd = -1;
        bool fallback_rumble = false;
        bool fallback_constant = false;
""",
                r"""
        int fallback_fd = -1;
        bool fallback_rumble = false;
        bool fallback_constant = false;
        bool fallback_periodic = false;
"""
            ),
            (
                r"""
            const bool rumble = InputBitSet(effect_bits, FF_RUMBLE);
            const bool constant = InputBitSet(effect_bits, FF_CONSTANT);
            if (!rumble && !constant) {
""",
                r"""
            const bool rumble = InputBitSet(effect_bits, FF_RUMBLE);
            const bool constant = InputBitSet(effect_bits, FF_CONSTANT);
            // Cirrus CS40L26 haptics offer neither, only periodic effects.
            const bool periodic = InputBitSet(effect_bits, FF_PERIODIC);
            if (!rumble && !constant && !periodic) {
"""
            ),
            (
                r"""
                fallback_rumble = rumble;
                fallback_constant = constant;
            } else {
""",
                r"""
                fallback_rumble = rumble;
                fallback_constant = constant;
                fallback_periodic = periodic;
            } else {
"""
            ),
            (
                r"""
            supports_rumble_ = fallback_rumble;
            supports_constant_ = fallback_constant;
        }
""",
                r"""
            supports_rumble_ = fallback_rumble;
            supports_constant_ = fallback_constant;
            supports_periodic_ = fallback_periodic;
        }
"""
            ),
            (
                r"""
        } else if (supports_constant_) {
            effect.type = FF_CONSTANT;
            effect.u.constant.level = 0x5fff;
        } else {
""",
                r"""
        } else if (supports_constant_) {
            effect.type = FF_CONSTANT;
            effect.u.constant.level = 0x5fff;
        } else if (supports_periodic_) {
            // A 10 ms sine at full magnitude, which the CS40L26 plays through its
            // buzz generator.
            effect.type = FF_PERIODIC;
            effect.u.periodic.waveform = FF_SINE;
            effect.u.periodic.period = 10;
            effect.u.periodic.magnitude = 0x7fff;
        } else {
"""
            ),
            (
                r"""
        effect_id_ = -1;
        supports_rumble_ = false;
        supports_constant_ = false;
    }
""",
                r"""
        effect_id_ = -1;
        supports_rumble_ = false;
        supports_constant_ = false;
        supports_periodic_ = false;
    }
"""
            ),
            (
                r"""
    bool supports_rumble_ = false;
    bool supports_constant_ = false;
    bool missing_device_logged_ = false;
""",
                r"""
    bool supports_rumble_ = false;
    bool supports_constant_ = false;
    bool supports_periodic_ = false;
    bool missing_device_logged_ = false;
"""
            ),
        ]
