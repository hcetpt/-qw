### SPDX 许可证标识符：GPL-2.0

==================================
非易失性内存运行时固件激活
==================================

一些持久内存设备会在设备（或称为“DIMM”）本地运行固件来执行诸如介质管理、容量配置和健康监控等任务。通常，更新该固件的过程涉及重启，因为这会影响到正在进行中的内存交易。然而，重启会造成中断，并且至少在英特尔持久内存平台的实现中——由英特尔 ACPI DSM 规范 [1] 描述——已经添加了支持在运行时激活固件的功能。

libnvdimm 实现了一个原生的 sysfs 接口，允许平台宣传并控制它们本地的运行时固件激活能力。
libnvdimm 总线对象 ndbusX 实现了一个 `ndbusX/firmware/activate` 属性，用来显示固件激活的状态，这些状态包括 'idle'、'armed'、'overflow' 和 'busy'：

- **idle**：
  没有设备被设置为准备激活固件。

- **armed**：
  至少有一个设备处于待命状态。

- **busy**：
  在此状态下，待命的设备正在从待命状态转换回空闲状态，并完成一个激活周期。

- **overflow**：
  如果平台有一种概念，即执行激活需要逐步进行的工作量，那么可能存在太多 DIMM 被设为待激活。在这种情况下，'overflow' 状态表示固件激活可能会超时。

`ndbusX/firmware/activate` 属性可以写入 'live' 或 'quiesce' 的值。'quiesce' 的值会触发内核从类似于休眠的 'freeze' 状态运行固件激活，在这个状态下驱动程序和应用程序会被通知停止对系统内存的修改。'live' 的值尝试在不经历休眠周期的情况下激活固件。如果未检测到任何固件激活能力，则完全省略 `ndbusX/firmware/activate` 属性。

另一个属性 `ndbusX/firmware/capability` 显示 'live' 或 'quiesce' 的值，其中 'live' 表示固件不需要或不会给系统带来任何静默期来更新固件。'quiesce' 的能力值表示固件期望并且会注入一个静默期用于内存控制器，但 'live' 仍然可以写入 `ndbusX/firmware/activate` 作为覆盖，以承担与正在进行中的设备和应用程序活动竞争的风险。如果未检测到任何固件激活能力，则完全省略 `ndbusX/firmware/capability` 属性。

libnvdimm 内存设备 / DIMM 对象 nmemX 实现了 `nmemX/firmware/activate` 和 `nmemX/firmware/result` 属性来传达每个设备的固件激活状态。与 `ndbusX/firmware/activate` 属性类似，`nmemX/firmware/activate` 属性指示 'idle'、'armed' 或 'busy'。当系统准备好激活固件、固件已就绪 + 状态设为待命，并且触发 `ndbusX/firmware/activate` 时，状态会从 'armed' 转换到 'idle'。在那之后的激活事件中，`nmemX/firmware/result` 属性反映最近一次激活的状态之一：

- **none**：
  自上次设备重置以来没有触发运行时激活。

- **success**：
  最近一次运行时激活成功完成。

- **fail**：
  最近一次运行时激活因特定于设备的原因失败。

- **not_staged**：
  最近一次运行时激活由于固件映像未就绪的顺序错误而失败。
need_reset:
  运行时固件激活失败，但仍然可以通过传统的系统电源循环方法来激活固件
[1]: https://docs.pmem.io/persistent-memory/
