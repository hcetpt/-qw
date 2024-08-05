... SPDX 许可证标识符: GPL-2.0

======================================
Chromebook 启动流程
======================================

大多数使用设备树的最新款 Chromebook 都采用了开源的 depthcharge_ 引导加载程序。Depthcharge_ 要求操作系统以 `FIT
映像`_ 的形式打包，其中包含操作系统映像以及一系列设备树。由 depthcharge_ 从 `FIT 映像`_ 中选择正确的设备树并将其提供给操作系统。
Depthcharge_ 用于选择设备树的方案考虑了以下三个变量：

- 板载名称，在 depthcharge_ 编译时指定。这在下面表示为 $(BOARD)
- 板载修订号，在运行时确定（可能是通过读取 GPIO 绑定，也可能是通过其他方法）。这在下面表示为 $(REV)
- SKU 号码，在启动时从 GPIO 绑定中读取。这在下面表示为 $(SKU)
对于最近的 Chromebook，depthcharge_ 创建了一个匹配列表，其格式如下：

- google,$(BOARD)-rev$(REV)-sku$(SKU)
- google,$(BOARD)-rev$(REV)
- google,$(BOARD)-sku$(SKU)
- google,$(BOARD)

请注意，一些较旧的 Chromebook 使用略有不同的列表，可能不包括 SKU 匹配或优先级不同。
值得注意的是，对于某些板载，可能存在额外的特定于板载的逻辑来向列表中注入额外的兼容字符串，但这种情况并不常见。
Depthcharge_ 将遍历 `FIT 映像`_ 中的所有设备树，试图找到与最具体的兼容字符串相匹配的设备树。然后，它将再次遍历 `FIT 映像`_ 中的所有设备树，试图找到与第二具体的兼容字符串相匹配的设备树，依此类推。
在搜索设备树时，depthcharge_ 不关心兼容字符串在设备树根兼容字符串数组中的位置。
举个例子，如果我们在 "lazor" 板载上，修订版 4，SKU 0，并且我们有两个设备树：

- "google,lazor-rev5-sku0", "google,lazor-rev4-sku0", "qcom,sc7180"
- "google,lazor", "qcom,sc7180"

那么即便 "google,lazor-rev4-sku0" 是该设备树中第二个列出的兼容字符串，depthcharge_ 也会选择第一个设备树。
这是因为它比 "google,lazor" 更具体。
应当注意的是，depthcharge_ 没有任何智能去尝试匹配那些“相近”的板级或 SKU 修订版本。也就是说，如果 depthcharge_ 知道它正在运行的是一块“rev4”版本的板子，但没有对应的“rev4”设备树，那么 depthcharge_ *不会* 去寻找“rev3”的设备树。通常情况下，当对一块板子做出任何重大改动时，即使这些改动不需要在设备树中体现，板级的修订号也会增加。因此，我们经常会看到有多个修订版本的设备树。

值得注意的是，考虑到 depthcharge_ 的上述机制，最灵活的做法是在支持最新版（或几个最新版）板子的设备树中省略 "-rev{REV}" 兼容字符串。这样做的结果是，当你拿到新版的板子并试图在其上运行旧软件时，系统会选择已知的最新设备树来使用。

.. _depthcharge: https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/depthcharge/
.. _`FIT Image`: https://doc.coreboot.org/lib/payloads/fit.html
