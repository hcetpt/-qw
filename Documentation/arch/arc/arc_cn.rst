### SPDX 许可证标识符: GPL-2.0

#### 针对 ARC 处理器的 Linux 内核
_____________________________________

##### 其他信息来源
______________________

以下是一些可以找到有关 ARC 处理器及其相关开源项目的更多信息的资源：
- `<https://embarc.org>`_ - 针对 ARC 的开源社区门户。这是开始寻找相关的自由和开源软件（FOSS）项目、工具链发布、新闻和其他内容的好地方。
- `<https://github.com/foss-for-synopsys-dwc-arc-processors>`_ - 所有与 ARC 处理器相关的开源项目开发活动的中心。其中一些项目是各种上游项目的分支，在提交给上游项目之前，这些分支会托管“正在进行的工作”。其他项目由新思科技开发，并作为开源提供给社区以供在 ARC 处理器上使用。
- `新思科技官方 ARC 处理器网站 <https://www.synopsys.com/designware-ip/processor-solutions.html>`_ - 提供访问一些 IP 文档（例如 ARC HS 处理器的《程序员参考手册》(PRM) <https://www.synopsys.com/dw/doc.php/ds/cc/programmers-reference-manual-ARC-HS.pdf>）和某些商业工具的免费版本（例如 Free nSIM <https://www.synopsys.com/cgi-bin/dwarcnsim/req1.cgi> 和 MetaWare Lite 版本 <https://www.synopsys.com/cgi-bin/arcmwtk_lite/reg1.cgi>）。请注意，访问文档和工具都需要注册。

##### 关于 ARC 处理器配置的重要说明
___________________________________

ARC 处理器具有高度的可配置性，并且 Linux 支持多种配置选项。有些选项对软件透明（例如缓存几何结构），有些可以在运行时检测到并进行相应的配置和使用，而有些则需要在内核配置工具（即“make menuconfig”）中明确选择或配置。但是，并非所有配置选项都支持 ARC 处理器运行 Linux。SoC 设计团队应参照 ARC HS 数据手册中的“附录 E：ARC Linux 的配置”来获取配置指南。遵循这些指南并提前选择有效的配置选项对于避免在 SoC 引导和一般软件开发过程中出现任何意外问题至关重要。
为 ARC 处理器构建 Linux 内核
############################################

为 ARC 处理器构建内核的过程与其他架构相同，可以通过以下两种方式完成：

- 交叉编译：在具有不同处理器架构（通常是 x86_64/amd64）的开发主机上为 ARC 目标进行编译的过程
- 本机编译：在 ARC 平台（硬件板或类似 QEMU 的模拟器）上为 ARC 进行编译的过程，该平台需安装完整的开发环境（如 GNU 工具链、dtc、make 等）

无论哪种情况，都需要针对主机的最新的 ARC GNU 工具链。
新思科技提供了可用于此目的的预构建工具链版本，可从以下链接获取：

- 新思科技 GNU 工具链发布：
  `<https://github.com/foss-for-synopsys-dwc-arc-processors/toolchain/releases>`_

- Linux 内核编译器集合：
  `<https://mirrors.edge.kernel.org/pub/tools/crosstool>`_

- Bootlin 的工具链集合： `<https://toolchains.bootlin.com>`_

安装完工具链后，请确保将其“bin”文件夹添加到您的 ``PATH`` 环境变量中。然后设置 ``ARCH=arc`` 和 ``CROSS_COMPILE=arc-linux``（或与已安装的 ARC 工具链前缀相匹配的内容），之后按照常规步骤执行 ``make defconfig && make``。
这将在内核源代码树的根目录生成“vmlinux”文件，可用于通过 JTAG 加载到目标系统上。
如果您需要一个适用于 U-Boot 引导加载程序的映像，请执行 ``make uImage``，将生成的 “uImage” 文件放置在 ``arch/arc/boot`` 文件夹中。
