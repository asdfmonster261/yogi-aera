from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "init: unpack the LGZ-packed ramdisk files at the start of second stage"
        self.target_file = "system/core/init/init.cpp"

        self.CHANGES = [
            (
                r"""
#include <sys/signalfd.h>
#include <sys/system_properties.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>
""",
                r"""
#include <sys/signalfd.h>
#include <sys/stat.h>
#include <sys/system_properties.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>
"""
            ),
            (
                r"""
    SelinuxSetupKernelLogging();

    // Update $PATH in the case the second stage init is newer than first stage init, where it is
    // first set.
""",
                r"""
    SelinuxSetupKernelLogging();

    // aera_build_callback.sh LGZ-packed most of the ramdisk; restore it before anything
    // else reads it. init and the libraries it links were left as they are.
    {
        struct stat lgz_st;
        if (stat("/lgz_compressed_files.txt", &lgz_st) == 0) {
            LOG(INFO) << "[LGZ] Starting early decompression of ramdisk files...";
            pid_t pid = fork();
            if (pid == 0) {
                execl("/system/bin/lgz", "lgz", "decompress_all",
                      "/lgz_compressed_files.txt", nullptr);
                _exit(127);
            } else if (pid > 0) {
                int wstatus;
                waitpid(pid, &wstatus, 0);
                if (WIFEXITED(wstatus) && WEXITSTATUS(wstatus) == 0) {
                    LOG(INFO) << "[LGZ] Decompression completed successfully";
                } else {
                    LOG(ERROR) << "[LGZ] Decompression failed, status=" << wstatus;
                }
            } else {
                PLOG(ERROR) << "[LGZ] fork() failed";
            }
        }
    }

    // Update $PATH in the case the second stage init is newer than first stage init, where it is
    // first set.
"""
            ),
        ]
