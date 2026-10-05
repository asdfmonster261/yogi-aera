from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "minuitwrp: drive the cover DSI panel on the fold"
        self.target_file = "bootable/recovery/minuitwrp/graphics_drm.cpp"

        # minui takes the first connected DSI, which is the inner panel, but only the
        # cover panel's touch controller probes in recovery. Prefer the DSI connector
        # with the higher connector_type_id (the cover); a single-panel device keeps
        # its only DSI.
        self.CHANGES = [
            (
                r"""    for (int i = 0; i < resources->count_connectors; i++) {
        drmModeConnector* connector = drmModeGetConnector(fd, resources->connectors[i]);
        if (connector) {
            if ((connector->connector_type == type) &&
                    (connector->connection == DRM_MODE_CONNECTED) &&
                    (connector->count_modes > 0))
                return connector;

            drmModeFreeConnector(connector);
        }
    }
    return nullptr;""",
                r"""    drmModeConnector* best = nullptr;
    for (int i = 0; i < resources->count_connectors; i++) {
        drmModeConnector* connector = drmModeGetConnector(fd, resources->connectors[i]);
        if (connector) {
            if ((connector->connector_type == type) &&
                    (connector->connection == DRM_MODE_CONNECTED) &&
                    (connector->count_modes > 0)) {
                if (!best || connector->connector_type_id > best->connector_type_id) {
                    if (best) drmModeFreeConnector(best);
                    best = connector;
                    continue;
                }
            }
            drmModeFreeConnector(connector);
        }
    }
    return best;"""
            )
        ]
