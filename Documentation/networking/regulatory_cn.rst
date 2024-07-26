... SPDX 许可证标识符: GPL-2.0

=======================================
Linux 无线法规文档
=======================================

本文档简要回顾了 Linux 无线法规架构的工作原理。
更多最新的信息可以在项目网页上找到：

https://wireless.wiki.kernel.org/en/developers/Regulatory

在用户空间中维护法规域
---------------------------------------

由于法规域的动态性质，我们将其保留在用户空间，并提供一个框架以供用户空间上传一个法规域到内核，作为所有无线设备应遵循的核心法规域。
如何将法规域传给内核
-------------------------------------------

当首次设置法规域时，内核会请求一个包含所有法规规则的数据库文件（regulatory.db）。然后，它会在需要查找特定国家的规则时使用该数据库。
如何将法规域传给内核（旧 CRDA 解决方案）
---------------------------------------------------------------

用户空间通过用户空间代理构建并发送法规域到内核。只有预期的法规域才会被内核接受。
目前可用的一个用户空间代理是 CRDA —— 中央法规域代理。关于它的文档如下：

https://wireless.wiki.kernel.org/en/developers/Regulatory/CRDA

基本上，当内核知道需要一个新的法规域时，它会发送一个 udev 事件。可以设置一个 udev 规则来触发 crda 发送对应于特定 ISO/IEC 3166 alpha2 的法规域。
下面是一个可用于此目的的 udev 规则示例：

# 示例文件，应放置在 /etc/udev/rules.d/regulatory.rules
KERNEL=="regulatory*", ACTION=="change", SUBSYSTEM=="platform", RUN+="/sbin/crda"

alpha2 作为环境变量 COUNTRY 提供。
谁会请求法规域？
--------------------------------

* 用户

用户可以使用 iw：

https://wireless.wiki.kernel.org/en/users/Documentation/iw

示例：

  # 设置法规域为“哥斯达黎加”
  iw reg set CR

这将请求内核设置法规域为指定的 alpha2。内核随后会向用户空间请求一个与用户指定的 alpha2 相对应的法规域，通过发送 uevent 实现。
* 无线子系统用于国家信息元素

内核会发送一个 uevent 来通知用户空间需要一个新的法规域。随着其集成的增加，后续将提供更多细节。
* 驱动程序

如果驱动程序确定它们需要设置一个特定的法规域，可以通过调用 regulatory_hint() 告知无线核心。
他们有两种选择——要么提供一个 alpha2，以便 crda 可以为该国家提供一个法规域；要么基于内部自定义知识构建自己的法规域，使无线核心能够遵守它。
大多数驱动程序将依赖于通过alpha2提供监管提示的第一种机制。对于这些驱动程序，可以根据自定义EEPROM监管数据使用额外的检查来确保符合性。这种额外的检查可以通过在它们的`struct wiphy`上注册一个`reg_notifier()`回调来实现。当核心的监管域发生变化时会调用这个通知器。驱动程序可以利用这一点来审查所做的更改以及审查是谁做出的更改（驱动程序、用户、国家信息元素），并根据其内部EEPROM数据确定允许什么。希望具备全球漫游能力的设备驱动程序应该使用此回调。关于全球漫游的更多信息将在支持该功能时添加到此文档中。

提供自己的内置监管域的设备驱动程序不需要回调，因为它们注册的信道是唯一被允许使用的信道，因此无法启用“额外”的信道。

示例代码：驱动程序提示alpha2：
------------------------------------------
以下示例来自zd1211rw设备驱动程序。您可以从设备EEPROM国家/监管域值到特定alpha2的映射开始，如下所示：

```c
static struct zd_reg_alpha2_map reg_alpha2_map[] = {
    { ZD_REGDOMAIN_FCC, "US" },
    { ZD_REGDOMAIN_IC, "CA" },
    { ZD_REGDOMAIN_ETSI, "DE" }, /* 通用ETSI，使用最严格的限制 */
    { ZD_REGDOMAIN_JAPAN, "JP" },
    { ZD_REGDOMAIN_JAPAN_ADD, "JP" },
    { ZD_REGDOMAIN_SPAIN, "ES" },
    { ZD_REGDOMAIN_FRANCE, "FR" },
};
```

然后，您可以定义一个函数来将读取的EEPROM值映射到alpha2，如下所示：

```c
static int zd_reg2alpha2(u8 regdomain, char *alpha2)
{
    unsigned int i;
    struct zd_reg_alpha2_map *reg_map;
    for (i = 0; i < ARRAY_SIZE(reg_alpha2_map); i++) {
        reg_map = &reg_alpha2_map[i];
        if (regdomain == reg_map->reg) {
            alpha2[0] = reg_map->alpha2[0];
            alpha2[1] = reg_map->alpha2[1];
            return 0;
        }
    }
    return 1;
}
```

最后，如果找到匹配项，则可以向核心提示发现的alpha2。您需要在注册您的`wiphy`之后执行此操作。您应该在初始化期间完成此操作：

```c
r = zd_reg2alpha2(mac->regdomain, alpha2);
if (!r)
    regulatory_hint(hw->wiphy, alpha2);
```

示例代码：提供内置监管域的驱动程序：
--------------------------------------------------------------
**注：**此API当前不可用，可以在需要时添加。

如果您有可以从驱动程序获取的监管信息，并且**需要**使用这些信息，我们允许您构建一个监管域结构并将其传递给无线核心。为此，您应该使用`kmalloc()`分配足够大的结构以容纳您的监管域结构，然后用您的数据填充它。最后，只需使用包含监管域结构的`regulatory_hint()`进行调用即可。
下面是使用堆栈缓存的监管域的一个简单示例。您的实现可能会有所不同（例如，从EEPROM读取缓存）。

例如，缓存某些监管域：

```c
struct ieee80211_regdomain mydriver_jp_regdom = {
    .n_reg_rules = 3,
    .alpha2 =  "JP",
    // .alpha2 =  "99", /* 如果我没有可映射的alpha2 */
    .reg_rules = {
        /* IEEE 802.11b/g, 信道1..14 */
        REG_RULE(2412-10, 2484+10, 40, 6, 20, 0),
        /* IEEE 802.11a, 信道34..48 */
        REG_RULE(5170-10, 5240+10, 40, 6, 20, NL80211_RRF_NO_IR),
        /* IEEE 802.11a, 信道52..64 */
        REG_RULE(5260-10, 5320+10, 40, 6, 20, NL80211_RRF_NO_IR|NL80211_RRF_DFS),
    }
};
```

然后，在注册您的`wiphy`之后的某段代码中：

```c
struct ieee80211_regdomain *rd;
int size_of_regd;
int num_rules = mydriver_jp_regdom.n_reg_rules;
unsigned int i;

size_of_regd = sizeof(struct ieee80211_regdomain) + (num_rules * sizeof(struct ieee80211_reg_rule));

rd = kzalloc(size_of_regd, GFP_KERNEL);
if (!rd)
    return -ENOMEM;

memcpy(rd, &mydriver_jp_regdom, sizeof(struct ieee80211_regdomain));

for (i=0; i < num_rules; i++)
    memcpy(&rd->reg_rules[i], &mydriver_jp_regdom.reg_rules[i], sizeof(struct ieee80211_reg_rule));
regulatory_struct_hint(rd);
```

静态编译的监管数据库
---------------------------------------
当数据库应该固定在内核中时，可以在构建时作为固件文件提供，然后链接到内核中。
