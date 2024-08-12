MMC 工具介绍
=============

有一个名为 mmc-utils 的 MMC 测试工具，该工具由 Ulf Hansson 维护，
你可以在下面的公共 git 仓库中找到它：

	https://git.kernel.org/pub/scm/utils/mmc/mmc-utils.git

功能
=====

mmc-utils 工具可以执行以下操作：

- 打印和解析 extcsd 数据
- 确定 eMMC 写保护状态
- 设置 eMMC 写保护状态
- 通过禁用仿真将 eMMC 数据扇区大小设置为 4KB
- 创建通用分区
- 启用增强型用户区域
- 按分区启用写可靠性
- 打印 STATUS_SEND（CMD13）的响应
- 启用启动分区
- 设置启动总线条件
- 启用 eMMC BKOPS 功能
- 永久启用 eMMC 硬件重置功能
- 永久禁用 eMMC 硬件重置功能
- 发送净化命令
- 为设备编程认证密钥
- 读取 rpmb 设备的计数器值到标准输出
- 从 rpmb 设备读取以输出
- 从数据文件写入 rpmb 设备
- 启用 eMMC 缓存功能
- 禁用 eMMC 缓存功能
- 打印并解析 CID 数据
- 打印并解析 CSD 数据
- 打印并解析 SCR 数据
