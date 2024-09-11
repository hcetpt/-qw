SPDX 许可证标识符: GPL-2.0+

=========================================
DRM 子系统的自动化测试
=========================================

简介
============

确保对核心或驱动程序的更改不会引入回归，在需要测试大量不同硬件配置的情况下，这可能非常耗时。此外，每个有兴趣进行此类测试的人都不得不获取和维护大量的硬件是不现实的。
另外，希望开发人员能够自己检查代码中的回归，而不是依赖于维护者找到它们并反馈。
在 gitlab.freedesktop.org 中有自动测试 Mesa 的设施，也可以用于测试 DRM 子系统。本文档解释了如何使用这种共享基础设施来节省大量时间和精力。

相关文件
==============

drivers/gpu/drm/ci/gitlab-ci.yml
--------------------------------

这是 GitLab CI 的根配置文件。除了其他不太重要的部分，它指定了要使用的脚本的具体版本。有一些变量可以修改以改变流水线的行为：

DRM_CI_PROJECT_PATH
    包含 CI 软件基础设施的 Mesa 仓库

DRM_CI_COMMIT_SHA
    从该仓库中使用的特定修订版本

UPSTREAM_REPO
    包含目标分支的 Git 仓库 URL

TARGET_BRANCH
    此分支将要合并的目标分支

IGT_VERSION
    从 https://gitlab.freedesktop.org/drm/igt-gpu-tools 获取的正在使用的 igt-gpu-tools 版本

drivers/gpu/drm/ci/testlist.txt
-------------------------------

所有驱动程序上运行的 IGT 测试（除非在驱动程序的 \*-skips.txt 文件中有提及，请参见下文）

drivers/gpu/drm/ci/${DRIVER_NAME}-${HW_REVISION}-fails.txt
----------------------------------------------------------

列出给定驱动程序在特定硬件修订版上的已知失败项

drivers/gpu/drm/ci/${DRIVER_NAME}-${HW_REVISION}-flakes.txt
-----------------------------------------------------------

列出给定驱动程序在特定硬件修订版上已知行为不可靠的测试。这些测试无论结果如何都不会导致任务失败。它们仍然会被运行
每个新的 flake 条目必须与一个链接关联，该链接指向报告受影响驱动程序作者的错误报告，以及板卡名称或设备树名称、受影响的第一个内核版本、用于测试的 IGT 版本及近似失败率
它们应采用以下格式提供：

```
# Bug Report: $LORE_OR_PATCHWORK_URL
# Board Name: broken-board.dtb
# Linux Version: 6.6-rc1
# IGT Version: 1.28-gd2af13d9f
# Failure Rate: 100
flaky-test
```

drivers/gpu/drm/ci/${DRIVER_NAME}-${HW_REVISION}-skips.txt
-----------------------------------------------------------

列出给定驱动程序在特定硬件修订版上不会运行的测试。这些通常是由于挂起机器、导致内存不足(OOM)、耗时过长等原因干扰测试列表运行的测试

如何在您的树上启用自动化测试
============================================

1. 如果您还没有在 https://gitlab.freedesktop.org/ 创建一个 Linux 树，请创建一个

2. 在您的内核仓库配置中（例如 https://gitlab.freedesktop.org/janedoe/linux/-/settings/ci_cd），将 CI/CD 配置文件从 .gitlab-ci.yml 更改为 drivers/gpu/drm/ci/gitlab-ci.yml
3. 请求加入 drm/ci-ok 组，以便您的用户具有在 https://gitlab.freedesktop.org/drm/ci-ok 上运行持续集成（CI）所需的权限。

4. 下次您向此仓库推送代码时，您将看到一个持续集成流水线被创建（例如：https://gitlab.freedesktop.org/janedoe/linux/-/pipelines）。

5. 各项任务将被执行，并且当流水线完成后，所有任务都应该是绿色的，除非发现了回退问题。

如何更新测试预期
=================

如果您对代码所做的更改修复了某些测试，那么您需要从 drivers/gpu/drm/ci/${DRIVER_NAME}_*_fails.txt 中的一个或多个文件中删除一行或多行，对于每个受更改影响的测试平台都需要进行这样的操作。

如何扩展覆盖率
=================

如果您的代码更改使得可以运行更多的测试（例如解决了可靠性问题），您可以从 flaky 测试列表和跳过列表中移除这些测试，然后如果有已知失败的情况，则更新预期结果。

如果需要更新所使用的 IGT 版本（也许您向其中添加了更多测试），请更新 gitlab-ci.yml 文件顶部的 IGT_VERSION 变量。

如何测试您对脚本的更改
=======================

为了测试 drm-ci 仓库中的脚本更改，您需要修改 drivers/gpu/drm/ci/gitlab-ci.yml 文件中的 DRM_CI_PROJECT_PATH 和 DRM_CI_COMMIT_SHA 变量，使其与您的项目分支对应（例如 janedoe/drm-ci）。这个分支需要位于 https://gitlab.freedesktop.org/ 中。

如何在测试中合并外部修复
=========================

通常，其他分支中的回退问题会阻止对当前测试分支的本地更改进行测试。这些修复会在构建任务中自动从目标分支上的一个名为 ${TARGET_BRANCH}-external-fixes 的分支合并进来。

如果流水线不在合并请求中，并且在本地分支中存在同名分支，则该分支的提交也会被合并进来。

如何处理可能宕机的自动化测试实验室
=================================

如果某个硬件农场宕机并导致本应通过的流水线失败，可以通过编辑 https://gitlab.freedesktop.org/gfx-ci/lab-status/-/blob/main/lab-status.yml 文件来禁用提交到该农场的所有任务。
