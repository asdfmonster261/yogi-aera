from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aera_remote: fit the whole frame in the browser window"
        self.target_file = "bootable/recovery/aera_remote/client/index.html"

        # The stage was a grid with only an implicit auto row, so the frame's
        # max-height:100% had nothing definite to resolve against and a tall frame
        # ran off the bottom of the page. One row and column sized to the stage
        # gives it one.
        self.CHANGES = [
            (
                r"""
.stage{min-height:0;display:grid;place-items:center}
""",
                r"""
.stage{min-height:0;display:grid;grid-template:minmax(0,1fr)/minmax(0,1fr);place-items:center}
"""
            ),
        ]
