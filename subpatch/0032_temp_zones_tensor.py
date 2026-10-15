from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: read the Tensor CPU zones as one averaged temperature"
        self.target_file = "bootable/recovery/aeraui/platform/temperature_reader.hpp"

        self.CHANGES = [
            (
                r"""
    if (name.compare(0, 12, "cpu-hw-trip-") == 0) return false;
    return name.compare(0, 4, "cpu-") == 0 || name.compare(0, 7, "cpullc-") == 0 ||
        name.compare(0, 4, "qmx-") == 0 || name == "cpu" || name == "cpu_thermal" ||
        name == "soc_thermal" || name == "soc-thermal" || name == "soc-therm";
""",
                r"""
    if (name.compare(0, 12, "cpu-hw-trip-") == 0) return false;
    // Tensor names its CPU zones BIG, MID, MIDLL and DSU; they appear once
    // thermal_stage has loaded the sensor module. soc_therm is the board
    // sensor rather than a CPU zone, and stays out of the average.
    if (name == "BIG" || name == "MID" || name == "MIDLL" || name == "DSU")
      return true;
    return name.compare(0, 4, "cpu-") == 0 || name.compare(0, 7, "cpullc-") == 0 ||
        name.compare(0, 4, "qmx-") == 0 || name == "cpu" || name == "cpu_thermal";
"""
            ),
            (
                r"""
    Temperatures result;
    for (const auto &path : cpu_) {
      long value = 0; std::ifstream input(path);
      if (!(input >> value)) continue;
      if (value > 0 && value <= 150) value *= 1000;
      if (value > 0 && value <= 150000)
        result.cpu = std::max(result.cpu, static_cast<int>(value));
    }
""",
                r"""
    Temperatures result;
    long cpu_sum = 0;
    int cpu_zones = 0;
    for (const auto &path : cpu_) {
      long value = 0; std::ifstream input(path);
      if (!(input >> value)) continue;
      if (value > 0 && value <= 150) value *= 1000;
      if (value > 0 && value <= 150000) {
        cpu_sum += value;
        ++cpu_zones;
      }
    }
    if (cpu_zones > 0)
      result.cpu = static_cast<int>(cpu_sum / cpu_zones);
"""
            ),
        ]
