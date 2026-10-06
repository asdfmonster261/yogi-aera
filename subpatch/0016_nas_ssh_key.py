from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "nas: log in to SFTP with an SSH key"
        self.target_file = "bootable/recovery/nas/NasManager.cpp"

        self.CHANGES = [
            (
                r"""
		if (!obscure_pass.empty())
			cfg << "pass = " << obscure_pass << "\n";

		cfg << "shell_type = unix\n";
""",
                r"""
		if (!obscure_pass.empty())
			cfg << "pass = " << obscure_pass << "\n";

		// Public-key login, with the key kept in root-only recovery storage rather
		// than shared storage.
		if (access("/data/recovery/AERA/nas/ssh_key", R_OK) == 0)
			cfg << "key_file = /data/recovery/AERA/nas/ssh_key\n";

		cfg << "shell_type = unix\n";
"""
            ),
        ]
