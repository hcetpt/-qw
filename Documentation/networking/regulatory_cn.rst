SPDX 许可证标识符: GPL-2.0

=======================================
Linux 无线法规文档
=======================================

本文档简要介绍了 Linux 无线法规基础设施的工作原理。
更多最新的信息可以在项目网页上找到：

https://wireless.wiki.kernel.org/en/developers/Regulatory

在用户空间中维护法规域
---------------------------------------

由于法规域的动态特性，我们将它们保存在用户空间，并提供一个框架以便用户空间上传一个作为中心核心法规域的法规域供所有无线设备遵循。

如何将法规域传给内核
-------------------------------------------

当法规域首次设置时，内核会请求一个包含所有法规规则的数据库文件（regulatory.db）。然后，它会在需要查找特定国家的规则时使用该数据库。

如何将法规域传给内核（旧的 CRDA 解决方案）
---------------------------------------------------------------

用户空间通过一个用户空间代理构建并发送法规域来将其传给内核。只有预期的法规域才会被内核接受。
目前可用的一个用户空间代理是 CRDA —— 中央法规域代理。其文档在这里：

https://wireless.wiki.kernel.org/en/developers/Regulatory/CRDA

基本上，当内核知道需要一个新的法规域时，它会发送一个 udev 事件。可以设置一个 udev 规则以触发 crda 发送特定 ISO/IEC 3166 alpha2 的相应法规域。
下面是一个可以使用的示例 udev 规则：

# 示例文件，应放置在 /etc/udev/rules.d/regulatory.rules
KERNEL=="regulatory*", ACTION=="change", SUBSYSTEM=="platform", RUN+="/sbin/crda"

alpha2 作为环境变量 COUNTRY 提供。

谁会请求法规域？
--------------------------------

* 用户

用户可以使用 `iw`：

https://wireless.wiki.kernel.org/en/users/Documentation/iw

示例：

  # 设置法规域为“哥斯达黎加”
  iw reg set CR

这将请求内核将法规域设置为指定的 alpha2。内核随后会通过发送 uevent 请求用户空间提供用户指定 alpha2 的法规域。
* 无线子系统用于国家信息元素

内核将发送一个 uevent 来通知用户空间需要一个新的法规域。随着集成的增加，会有更多的相关信息添加。
* 驱动程序

如果驱动程序确定需要设置特定的法规域，它们可以使用 `regulatory_hint()` 告知无线核心。
它们有两个选项——要么提供一个 alpha2，让 crda 提供该国家的法规域；要么根据内部自定义知识构建自己的法规域，使无线核心能够遵循。
* 大多数驱动程序将依赖于通过alpha2提供监管提示的第一种机制。对于这些驱动程序，可以根据自定义EEPROM监管数据使用一个额外的检查来确保符合性。这个额外的检查可以通过在它们的struct wiphy上注册一个reg_notifier()回调函数来实现。当核心的监管域发生变化时，此通知器会被调用。驱动程序可以利用此功能来审查所做的更改以及审查是谁做的更改（驱动程序、用户、国家信息元素），并根据其内部EEPROM数据确定允许哪些操作。希望具备全球漫游能力的设备驱动程序应该使用此回调。关于全球漫游的更多内容将在支持该功能后添加到此文档中。

提供自己内置监管域的设备驱动程序不需要回调，因为由它们注册的频道是唯一被允许使用的，因此无法启用*额外*的频道。

示例代码 - 驱动程序提示alpha2：
------------------------------------------
此示例来自zd1211rw设备驱动程序。您可以从将设备的EEPROM国家/监管域值映射到特定alpha2开始如下：

```c
static struct zd_reg_alpha2_map reg_alpha2_map[] = {
    { ZD_REGDOMAIN_FCC, "US" },
    { ZD_REGDOMAIN_IC, "CA" },
    { ZD_REGDOMAIN_ETSI, "DE" }, /* 泛ETSI，使用最严格的 */
    { ZD_REGDOMAIN_JAPAN, "JP" },
    { ZD_REGDOMAIN_JAPAN_ADD, "JP" },
    { ZD_REGDOMAIN_SPAIN, "ES" },
    { ZD_REGDOMAIN_FRANCE, "FR" }
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

最后，如果找到了匹配项，则可以向核心提示您发现的alpha2。您需要在注册您的wiphy之后执行此操作，并且应在初始化期间完成此操作：

```c
r = zd_reg2alpha2(mac->regdomain, alpha2);
if (!r)
    regulatory_hint(hw->wiphy, alpha2);
```

示例代码 - 提供内置监管域的驱动程序：
--------------------------------------------------------------
[注意：此API当前不可用，可在需要时添加]

如果您有可以从驱动程序获取的监管信息，并且*需要*使用此信息，我们可以让您构建一个监管域结构并将其传递给无线核心。为此，您应该使用kmalloc()分配足够大的空间来容纳您的监管域结构，然后填写您的数据。最后，只需调用regulatory_hint()并将监管域结构作为参数传递即可。
下面是一个简单的示例，其中使用堆栈缓存了监管域。您的实现可能会有所不同（例如，从EEPROM缓存读取）。
示例缓存了一些监管域：

```c
struct ieee80211_regdomain mydriver_jp_regdom = {
    .n_reg_rules = 3,
    .alpha2 =  "JP",
    //.alpha2 =  "99", /* 如果我没有可映射的alpha2 */
    .reg_rules = {
        /* IEEE 802.11b/g，频道1至14 */
        REG_RULE(2412-10, 2484+10, 40, 6, 20, 0),
        /* IEEE 802.11a，频道34至48 */
        REG_RULE(5170-10, 5240+10, 40, 6, 20, NL80211_RRF_NO_IR),
        /* IEEE 802.11a，频道52至64 */
        REG_RULE(5260-10, 5320+10, 40, 6, 20, NL80211_RRF_NO_IR|NL80211_RRF_DFS)
    }
};
```

然后，在您的wiphy注册之后的某个代码部分：

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
当数据库应固定在内核中时，可以在构建时将其作为一个固件文件链接到内核中。
