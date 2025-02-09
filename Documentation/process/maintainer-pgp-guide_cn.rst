_PGP指南：

===========================
内核维护者PGP指南
===========================

:作者: 康斯坦丁·里巴特塞夫 <konstantin@linuxfoundation.org>

本文件主要面向Linux内核开发者，特别是子系统维护者。它包含了由Linux基金会发布的更全面的"`保护代码完整性`_"指南中讨论的部分信息。请参阅该文档以获取有关本指南中提到的一些主题的更深入讨论。
.. _`保护代码完整性`: https://github.com/lfit/itpol/blob/master/protecting-code-integrity.md

PGP在Linux内核开发中的作用
===========================================

PGP有助于确保由Linux内核开发社区产生的代码的完整性，并且在较小程度上，通过PGP签名电子邮件交换来建立开发者之间的可信通信渠道。Linux内核源代码以两种主要格式提供：

- 分布式源代码仓库（git）
- 定期发布快照（tarball）

git仓库和tarball都带有官方内核发布者创建的内核开发者的PGP签名。这些签名提供了加密保证，即通过kernel.org或其他任何镜像站提供的可下载版本与这些开发者工作站上的内容完全相同。为此：

- git仓库为所有标签提供PGP签名
- tarball为所有下载提供独立的PGP签名

.. _devs_not_infra:

信任开发者而非基础设施
-------------------------------------------

自2011年核心kernel.org系统的被入侵以来，Kernel Archives项目的首要运营原则一直是假设基础设施的任何部分随时可能被破坏。因此，管理员们采取了刻意措施强调信任必须始终放在开发者身上，而不是放在代码托管基础设施上，无论后者的安全实践有多好。
上述指导原则是需要本指南的原因。我们希望确保通过将信任置于开发者身上，我们不会简单地将未来潜在的安全事件的责任推给其他人。目标是提供一套指导方针，开发者可以使用这些方针来创建一个安全的工作环境，并保护用于确保Linux内核本身完整性的PGP密钥。

.. _pgp_tools:

PGP工具
=========

使用GnuPG 2.2或更高版本
----------------------

您的发行版应该已经默认安装了GnuPG，您只需要验证是否使用了一个合理的最新版本。
要检查，请运行：
```bash
$ gpg --version | head -n1
```
如果您有2.2或更高版本，则可以直接使用。如果您使用的版本低于2.2，则本指南中的某些命令可能无法工作。
配置gpg-agent选项
~~~~~~~~~~~~~~~~~~~~~~~~~~~

GnuPG代理是一个辅助工具，在您使用`gpg`命令时会自动启动并在后台运行，目的是缓存私钥密码。您需要了解两个选项以调整密码从缓存中过期的时间：

- `default-cache-ttl`（秒）：如果您在时间存活期内再次使用相同的密钥，计时器将重置为另一个周期。默认值为600秒（10分钟）。
- `max-cache-ttl`（秒）：无论您从首次输入密码以来使用密钥的频率如何，如果最大时间存活期计数到期，您将需要重新输入密码。默认值为1800秒（30分钟）。
如果你觉得这些默认时间太短（或太长），你可以编辑你的 ``~/.gnupg/gpg-agent.conf`` 文件来设置你自己的值：

    # 设置为30分钟作为常规ttl，2小时作为最大ttl
    default-cache-ttl 1800
    max-cache-ttl 7200

.. note::

    再也不需要在shell会话开始时手动启动gpg-agent了。
    你可能想要检查你的rc文件，移除任何为旧版本GnuPG设置的内容，
    因为它们可能不再执行正确的事情。

.. _protect_your_key:

保护你的PGP密钥
====================

本指南假设你已经有一个用于Linux内核开发的PGP密钥。如果你还没有一个，请参考前面提到的"`保护代码完整性`_"文档中的指导来创建一个新的密钥。
如果你当前的密钥弱于2048位（RSA），你也应该创建一个新的密钥。
理解PGP子密钥
-------------------------

一个PGP密钥很少只由单一密钥对组成——通常它是一组独立的子密钥，可以根据它们创建时赋予的不同能力用于不同的目的。
PGP定义了四种密钥可以拥有的能力：

- **[S]** 密钥可用于签名
- **[E]** 密钥可用于加密
- **[A]** 密钥可用于认证
- **[C]** 密钥可用于认证其他密钥

具有**[C]**能力的密钥通常被称为“主”密钥，但这种术语可能会产生误导，因为它暗示认证密钥可以用作该链上其他任何子密钥的替代（就像物理“主”密钥可以打开为其他密钥制作的锁一样）。
由于情况并非如此，本指南将称之为“认证密钥”，以避免任何混淆。
至关重要的是要完全理解以下内容：

1. 所有子密钥都是完全独立的。如果你丢失了一个私有子密钥，不能从你的链上的任何其他私有密钥恢复或重新创建它。
2. 除了认证密钥外，可以有多个相同能力的子密钥（例如，你可以有两个有效的加密子密钥，三个有效的签名子密钥，但只有一个有效的认证子密钥）。所有子密钥都是完全独立的——用一个**[E]**子密钥加密的消息不能用你可能有的任何其他**[E]**子密钥解密。
3. 单个子密钥可以拥有多种能力（例如，你的**[C]**密钥也可以是你的**[S]**密钥）。
携带**[C]**（认证）能力的密钥是唯一可以用来表明与其他密钥关系的密钥。只有**[C]**密钥可以用于：

- 添加或撤销其他具有S/E/A能力的密钥（子密钥）
- 添加、更改或撤销与密钥关联的身份（uids）
- 添加或更改自身的过期日期或任何子密钥的过期日期
- 为了信任网络的目的签署其他人的密钥

默认情况下，生成新密钥时GnuPG会创建如下内容：

- 一个同时具有认证和签名能力的子密钥（**[SC]**）
- 一个单独的具有加密能力的子密钥（**[E]**）

如果你使用默认参数生成密钥，那么这就是你会得到的。你可以通过运行 ``gpg --list-secret-keys`` 来验证，例如：

    sec   ed25519 2022-12-20 [SC] [expires: 2024-12-19]
          000000000000000000000000AAAABBBBCCCCDDDD
    uid           [ultimate] Alice Dev <adev@kernel.org>
    ssb   cv25519 2022-12-20 [E] [expires: 2024-12-19]

在``sec``条目下的长行是你密钥的指纹——
下面示例中出现的``[fpr]``所指的就是这40个字符的字符串。
确保你的密码短语足够强大
----------------------------

GnuPG 使用密码短语在存储私钥到磁盘之前对其进行加密。这样一来，即使你的 ``.gnupg`` 目录被泄露或被盗，攻击者也无法在未首先获得解密私钥所需的密码短语的情况下使用这些私钥。
保护你的私钥具有强大的密码短语是绝对必要的。要设置它或更改它，请使用以下命令：

    $ gpg --change-passphrase [fpr]

创建独立的签名子密钥
----------------------------

我们的目标是通过将其移至离线媒体来保护你的认证密钥，因此如果你只有一个组合的 **[SC]** 密钥，则应该创建一个独立的签名子密钥：

    $ gpg --quick-addkey [fpr] ed25519 sign

.. note:: GnuPG 中的 ECC 支持

    注意，如果你打算使用不支持 ED25519 ECC 密钥的硬件令牌，则应选择 "nistp256" 而不是 "ed25519"。请参阅下面关于推荐硬件设备的部分。
备份你的认证密钥以备灾难恢复
----------------------------------------------

你从其他开发者处获得的 PGP 密钥上的签名越多，你就越有必要创建一个不在数字媒介上的备份版本，以备灾难恢复之需。
创建你的私钥可打印硬拷贝的最佳方式是使用为此目的编写的 `paperkey` 软件。有关输出格式及其相对于其他解决方案的优势，请参阅 `man paperkey`。Paperkey 应该已经被大多数发行版打包。
运行以下命令以创建你的私钥的硬拷贝备份：

    $ gpg --export-secret-key [fpr] | paperkey -o /tmp/key-backup.txt

将该文件打印出来（或者直接将输出管道到 lpr），然后拿一支笔，在纸张的边缘写下你的密码短语。**强烈建议这样做**，因为密钥打印件仍然使用该密码短语进行加密，并且如果你更改了它，当你需要恢复备份时很可能忘记了原来的密码短语 —— 这是肯定的。
将打印出来的结果和手写的密码短语放入信封中，并存放在安全且妥善保护的地方，最好远离你的住所，比如银行保险箱。
.. note::

    你的打印机可能不再是一个简单的连接到并行端口的简单设备，但由于输出仍然使用你的密码短语进行加密，即使打印到“云集成”的现代打印机也应该是相对安全的操作。
备份你的整个 GnuPG 目录
----------------------------------

.. warning::

    **!!!不要跳过此步骤!!!**

拥有随时可用的 PGP 密钥备份很重要，以防你需要恢复它们。这与我们使用 `paperkey` 所做的灾难级别准备不同。每当需要使用你的认证密钥时——例如更改自己的密钥或将其他人的密钥签名在会议和峰会后——你也会依赖这些外部副本。
首先获取一个小的 USB “拇指”驱动器（最好是两个！），用于备份目的。你需要使用 LUKS 对其进行加密——请参阅你的发行版文档了解如何完成此操作。
对于加密密码短语，你可以使用与你的 PGP 密钥相同的密码。
一旦加密过程完成，重新插入U盘并确保它被正确挂载。将你的整个``.gnupg``目录复制到加密存储中：

    $ cp -a ~/.gnupg /media/disk/foo/gnupg-backup

现在你应该测试一下以确保一切仍然正常工作：

    $ gpg --homedir=/media/disk/foo/gnupg-backup --list-key [fpr]

如果没有出现任何错误，那么应该就可以正常使用了。卸载U盘，并明确标记它以免下次需要使用随机U盘时误删，然后放在一个安全的地方——但不要放得太远，因为你偶尔会需要它来编辑身份信息、添加或撤销子密钥，或者签署他人的密钥。
移除认证密钥从家目录中
----------------------------------------

我们家目录中的文件并不像我们想象的那样得到很好的保护。它们可以通过许多不同的方式泄露或窃取：

- 在快速复制家目录设置新工作站时意外泄露
- 系统管理员的疏忽或恶意行为
- 通过保护不当的备份
- 桌面应用程序（浏览器、PDF阅读器等）中的恶意软件
- 在跨国境时受到强迫

用良好的密码短语保护你的密钥可以大大降低以上任何一种风险，但密码短语可能通过键盘记录器、肩窥或许多其他方式被发现。因此，推荐的做法是将你的认证密钥从家目录中移除并存储在离线存储中
.. warning::

    请参阅前面的部分并确保你已经完全备份了GnuPG目录。我们即将要做的操作会使你的密钥无法使用，除非你有可用的备份！

首先，识别你的认证密钥的Keygrip：

    $ gpg --with-keygrip --list-key [fpr]

输出将是这样的：

    pub   ed25519 2022-12-20 [SC] [expires: 2022-12-19]
          000000000000000000000000AAAABBBBCCCCDDDD
          Keygrip = 1111000000000000000000000000000000000000
    uid           [ultimate] Alice Dev <adev@kernel.org>
    sub   cv25519 2022-12-20 [E] [expires: 2022-12-19]
          Keygrip = 2222000000000000000000000000000000000000
    sub   ed25519 2022-12-20 [S]
          Keygrip = 3333000000000000000000000000000000000000

找到“pub”行下面的Keygrip条目（就在认证密钥指纹正下方）。这将直接对应于你在``~/.gnupg``目录中的一个文件：

    $ cd ~/.gnupg/private-keys-v1.d
    $ ls
    1111000000000000000000000000000000000000.key
    2222000000000000000000000000000000000000.key
    3333000000000000000000000000000000000000.key

你只需要简单地移除与认证密钥Keygrip对应的.key文件：

    $ cd ~/.gnupg/private-keys-v1.d
    $ rm 1111000000000000000000000000000000000000.key

现在，如果你发出``--list-secret-keys``命令，它将显示认证密钥已缺失（“#”表示它不可用）：

    $ gpg --list-secret-keys
    sec#  ed25519 2022-12-20 [SC] [expires: 2024-12-19]
          000000000000000000000000AAAABBBBCCCCDDDD
    uid           [ultimate] Alice Dev <adev@kernel.org>
    ssb   cv25519 2022-12-20 [E] [expires: 2024-12-19]
    ssb   ed25519 2022-12-20 [S]

你还应该移除``~/.gnupg``目录中的任何``secring.gpg``文件，这些文件可能是GnuPG旧版本留下的
如果你没有"private-keys-v1.d"目录
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果你没有``~/.gnupg/private-keys-v1.d``目录，那么你的私钥仍然存储在GnuPG v1使用的遗留``secring.gpg``文件中。对你的密钥进行任何更改，如更改密码短语或添加子密钥，都应自动将旧的``secring.gpg``格式转换为使用``private-keys-v1.d``。

一旦你完成了这些操作，请确保删除过时的``secring.gpg``文件，因为它仍然包含你的私钥。
.. _智能卡:

将子密钥移到专用加密设备上
=============================================

尽管认证密钥现在已经安全地防止泄露或窃取，但是子密钥仍然存在于家目录中。任何人只要能够获取到这些子密钥，就能够解密你的通信或伪造你的签名（如果他们知道密码短语的话）。此外，每次执行GnuPG操作时，密钥都会加载到系统内存中，并且可能会被足够先进的恶意软件从中窃取（想想熔毁和幽灵）
完全保护你的密钥的最佳方法是将它们移动到能够执行智能卡操作的专用硬件设备上
智能卡的好处
--------------------------

智能卡包含一个能够存储私钥并在卡片本身上直接执行加密操作的加密芯片。因为密钥内容从未离开智能卡，所以你插入硬件设备的计算机的操作系统无法检索私钥本身。这与我们之前用于备份目的的加密USB存储设备非常不同——当该USB设备插上并挂载时，操作系统能够访问私钥内容
使用外部加密USB媒体不能替代拥有支持智能卡功能的设备
可用的智能卡设备
---------------------------

除非所有你的笔记本电脑和工作站都有智能卡读卡器，否则最简单的方法是获得一个专门的USB设备来实现智能卡功能。有几个选项可供选择：

- `Nitrokey Start`_: 开放硬件和自由软件，基于FSI日本的`Gnuk`_. 是少数几个支持ED25519 ECC密钥的商业可用设备之一，但提供的安全特性最少（例如抵抗篡改或某些侧信道攻击的能力）
`Nitrokey Pro 2`：与 Nitrokey Start 类似，但防篡改能力更强，并提供了更多的安全特性。Pro 2 支持 ECC 加密（NISTP）。
- `Yubikey 5`：专有的硬件和软件，但比 Nitrokey Pro 更便宜，并且有 USB-C 形式的版本，对于新型笔记本电脑更为实用。它提供了额外的安全功能，如 FIDO U2F 等，并且现在终于支持了 NISTP 和 ED25519 ECC 密钥。

您的选择将取决于成本、您所在地区的发货可用性以及对开源/专有硬件的考虑。
.. note::

    如果您在 MAINTAINERS 列表中或在 kernel.org 拥有账户，则您有资格免费获得 `Nitrokey Start`_，这是来自 Linux 基金会的福利。
.. _`Nitrokey Start`: https://shop.nitrokey.com/shop/product/nitrokey-start-6
.. _`Nitrokey Pro 2`: https://shop.nitrokey.com/shop/product/nkpr2-nitrokey-pro-2-3
.. _`Yubikey 5`: https://www.yubico.com/products/yubikey-5-overview/
.. _Gnuk: https://www.fsij.org/doc-gnuk/
.. _`qualify for a free Nitrokey Start`: https://www.kernel.org/nitrokey-digital-tokens-for-kernel-developers.html

配置您的智能卡设备
-------------------

一旦您将智能卡插入到任何现代 Linux 工作站上，它应该能即刻工作。您可以通过以下命令来验证是否正常工作：

    $ gpg --card-status

如果能看到完整的智能卡详细信息，那么就可以正常使用了。
不幸的是，解决所有可能造成问题的原因超出了本指南的范围。如果您在尝试让卡片与 GnuPG 正常工作时遇到困难，请通过常规的支持渠道寻求帮助。
要配置您的智能卡，您需要使用 GnuPG 的菜单系统，因为没有方便的命令行选项：

    $ gpg --card-edit
    [...省略...]
    gpg/card> admin
    允许执行管理员命令
    gpg/card> passwd

您应该设置用户 PIN（1）、管理员 PIN（3）和重置码（4）。
请确保记录并妥善保存这些密码——尤其是管理员 PIN 和重置码（后者允许您彻底擦除智能卡）。由于很少需要用到管理员 PIN，如果不做记录，您很容易忘记它。
返回到主菜单后，您还可以设置其他值（如姓名、性别、登录数据等），但这不是必须的，并且如果智能卡丢失可能会泄露关于智能卡的信息。
.. note::

    尽管名字中包含“PIN”，但智能卡上的用户 PIN 和管理员 PIN 并不需要是数字。
.. warning::

    某些设备可能要求您先将子密钥移至设备上，然后才能更改密码短语。请查阅设备制造商提供的文档。
移动子密钥到您的智能卡
----------------------------------

退出卡片菜单（使用"q"键），并保存所有更改。接下来，让我们将您的子密钥移到智能卡上。大多数操作需要您的PGP密钥密码短语和卡片的管理员PIN码：

    $ gpg --edit-key [fpr]

    秘密子密钥可用
pub  ed25519/AAAABBBBCCCCDDDD
         创建于: 2022-12-20  过期: 2024-12-19  使用: SC
         信任: 最终        有效性: 最终
    ssb  cv25519/1111222233334444
         创建于: 2022-12-20  过期: 永不过期     使用: E
    ssb  ed25519/5555666677778888
         创建于: 2017-12-07  过期: 永不过期     使用: S
    [最终] (1). Alice Dev <adev@kernel.org>

    gpg>

使用``--edit-key``会再次进入菜单模式，并且您会注意到密钥列表略有不同。从这里开始，所有命令都在此菜单模式中完成，如“gpg>”所示。首先，选择要放到卡片上的密钥——您可以通过输入``key 1``（它是列表中的第一个，即**[E]**子密钥）来实现这一点：

    gpg> key 1

在输出中，您现在应该看到**[E]**密钥旁边有``ssb*``。星号``*``表示当前“选定”的密钥。它起到一个切换的作用，也就是说如果您再次输入``key 1``，星号``*``将会消失，密钥不再被选中。
现在，让我们将该密钥移到智能卡上：

    gpg> keytocard
    请选择存放密钥的位置：
       (2) 加密密钥
    您的选择？ 2

由于这是我们的**[E]**密钥，将其放入加密槽是有道理的。当您提交选择后，系统将首先提示您输入PGP密钥密码短语，然后是管理员PIN码。如果命令无错误返回，则密钥已被移动。
**重要**：现在再次输入``key 1``以取消选择第一个密钥，然后输入``key 2``以选择**[S]**密钥：

    gpg> key 1
    gpg> key 2
    gpg> keytocard
    请选择存放密钥的位置：
       (1) 签名密钥
       (3) 身份验证密钥
    您的选择？ 1

您可以使用**[S]**密钥进行签名和身份验证，但我们希望确保它位于签名槽中，因此选择(1)。同样，如果您的命令没有错误返回，则操作成功：

    gpg> q
    是否保存更改？ (y/N) y

保存更改会从您的主目录中删除已移到卡片的密钥（但这没关系，因为我们有备份，万一需要为替换智能卡再次执行此操作）
验证密钥是否已移动
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果您现在执行``--list-secret-keys``，您会发现输出中有一个细微差别：

    $ gpg --list-secret-keys
    sec#  ed25519 2022-12-20 [SC] [过期: 2024-12-19]
          000000000000000000000000AAAABBBBCCCCDDDD
    uid           [最终] Alice Dev <adev@kernel.org>
    ssb>  cv25519 2022-12-20 [E] [过期: 2024-12-19]
    ssb>  ed25519 2022-12-20 [S]

``ssb>``输出中的``>``表示子密钥仅在智能卡上可用。如果您回到秘密密钥目录并查看其中的内容，您会注意到那里的``.key``文件已经被存根替换：

    $ cd ~/.gnupg/private-keys-v1.d
    $ strings *.key | grep 'private-key'

输出应包含``shadowed-private-key``以指示这些文件只是存根，实际内容位于智能卡上。
验证智能卡是否正常工作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

为了验证智能卡是否按预期工作，您可以创建一个签名：

    $ echo "Hello world" | gpg --clearsign > /tmp/test.asc
    $ gpg --verify /tmp/test.asc

这将在您的第一条命令中要求您输入智能卡PIN码，然后在运行``gpg --verify``后显示"良好的签名"。
恭喜您，您已经成功地使窃取您的数字开发者身份变得极其困难！

其他常见的GnuPG操作
-----------------------------

以下是您使用PGP密钥时需要执行的一些常见操作的快速参考。
挂载您的安全离线存储
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

对于下面的所有操作，您都需要您的认证密钥，因此您需要先挂载备份离线存储并告诉GnuPG使用它：

    $ export GNUPGHOME=/media/disk/foo/gnupg-backup
    $ gpg --list-secret-keys

您需要确保输出中显示的是``sec``而不是``sec#``（``#``意味着密钥不可用，您仍然在使用常规的主目录位置）。
### 延长密钥过期日期

Certify 密钥默认从创建之日起两年后过期。这样做既出于安全考虑，也是为了让过时的密钥最终从密钥服务器上消失。
要将你的密钥过期时间从当前日期延长一年，只需运行：

    $ gpg --quick-set-expire [fpr] 1y

你也可以指定一个具体的日期，如果这更容易记住（例如你的生日、1月1日或加拿大国庆日）：

    $ gpg --quick-set-expire [fpr] 2025-07-01

记得将更新后的密钥重新发送到密钥服务器：

    $ gpg --send-key [fpr]

### 在任何更改后更新工作目录

当你使用离线存储对密钥进行了任何更改之后，你需要将这些更改重新导入到你的常规工作目录中：

    $ gpg --export | gpg --homedir ~/.gnupg --import
    $ unset GNUPGHOME

### 通过SSH转发gpg-agent

如果你需要在远程系统上签署标签或提交，你可以通过SSH转发你的gpg-agent。请参考GnuPG Wiki提供的说明：

- [通过SSH转发代理](https://wiki.gnupg.org/AgentForwarding)

如果你能够在远程端修改sshd服务器设置，它会更顺畅地工作。

### 使用PGP与Git

Git的一个核心特性是其去中心化的特点——一旦仓库被克隆到你的系统上，你就拥有了项目的完整历史记录，包括所有的标签、提交和分支。但是，面对数百个克隆的仓库，如何验证你的linux.git副本没有被恶意第三方篡改？

或者如果代码中发现了一个后门，而提交中的“作者”一栏显示是你做的，而你确信自己与此无关，该怎么办？

为了解决这两个问题，Git引入了PGP集成。签名的标签通过确保仓库内容与创建标签的开发人员工作站上的内容完全相同来证明仓库的完整性，而签名的提交使得没有访问你的PGP密钥的人几乎不可能冒充你。

#### 配置Git使用你的PGP密钥

如果你的密钥环中只有一个私钥，那么你不需要做额外的工作，因为它会成为你的默认密钥。但是，如果你有多个私钥，你可以告诉Git应该使用哪个密钥（`[fpr]` 是你的密钥指纹）：

    $ git config --global user.signingKey [fpr]

#### 如何处理已签名的标签

要创建一个已签名的标签，只需在标签命令中传递 `-s` 参数：

    $ git tag -s [tagname]

我们建议总是签署Git标签，因为这样可以让其他开发者确认他们拉取的Git仓库没有被恶意篡改。

#### 如何验证已签名的标签

要验证一个已签名的标签，只需使用 `verify-tag` 命令：

    $ git verify-tag [tagname]

如果你从项目的另一个分支拉取标签，Git应该会自动在你拉取的尖端验证签名，并在合并操作期间向你展示结果：

    $ git pull [url] tags/sometag

合并消息将包含类似以下内容：

    Merge tag 'sometag' of [url]

    [标签信息]

    # gpg: 签名于 [...]
    # gpg: [fpr] 的良好签名

如果你正在验证别人的Git标签，则需要导入他们的PGP密钥。请参阅下面的 “[验证身份]” 部分。

#### 配置Git始终签署注释标签

如果你创建注释标签，你可能想要签署它。要强制Git始终签署注释标签，可以设置全局配置选项：

    $ git config --global tag.forceSignAnnotated true

#### 如何处理已签名的提交

创建已签名的提交很容易，但在Linux内核开发中使用它们却更加困难，因为它依赖于发送到邮件列表的补丁，而这种工作流程不会保留PGP提交签名。此外，在为了与上游同步而重置你的仓库时，即使是你的PGP提交签名也会被丢弃。因此，大多数内核开发者不费心签署他们的提交，并且会忽略他们在工作中依赖的外部仓库中的已签名提交。

然而，如果你的Git工作树在某个Git托管服务（如kernel.org、infradead.org、ozlabs.org或其他）上公开可用，那么建议你签署所有你的Git提交，即使上游开发者不能直接从中受益。

我们推荐这样做是因为以下原因：

1. 如果将来需要进行代码取证或追踪代码来源，即使是外部维护的带有PGP提交签名的树也将非常有价值。
2. 如果你以后需要重新克隆本地仓库（例如，在磁盘故障后），这使你可以在恢复工作前轻松验证仓库的完整性。
3. 如果有人需要挑选你的提交，这允许他们在应用提交前快速验证其完整性。
创建签名的提交
~~~~~~~~~~~~~~

要创建一个签名的提交，只需在`git commit`命令中添加``-S``参数（注意是大写的``-S``，因为与另一个标志冲突）：

    $ git commit -S

配置git以始终对提交进行签名
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

你可以告诉git始终对提交进行签名：

    git config --global commit.gpgSign true

.. note::

    在启用此功能之前，请确保你已经配置了``gpg-agent``。
.. _verify_identities:

如何处理已签名的补丁
----------------------

可以使用你的PGP密钥来签署发送给内核开发者邮件列表的补丁。由于现有的电子邮件签名机制（PGP-Mime或PGP-inline）往往会引发常规代码审查任务中的问题，你应该使用为此目的由kernel.org创建的工具，该工具将加密证明签名放入消息头（类似于DKIM）：

- `Patatt Patch Attestation`_

.. _`Patatt Patch Attestation`: https://pypi.org/project/patatt/

安装和配置patatt
~~~~~~~~~~~~~~~~

Patatt已经被许多发行版打包，因此请首先检查这些发行版。也可以使用"``pip install patatt``"从PyPI安装它。如果你已经通过git（通过``user.signingKey``配置参数）配置了PGP密钥，那么patatt不需要进一步的配置。你可以通过在想要的仓库中安装git-send-email钩子开始签署你的补丁：

    patatt install-hook

现在任何使用``git send-email``发送的补丁都将自动用你的加密签名进行签署。
检查patatt签名
~~~~~~~~~~~~~~

如果你正在使用``b4``来获取和应用补丁，那么它会自动尝试验证所有遇到的DKIM和patatt签名，例如：

    $ b4 am 20220720205013.890942-1-broonie@kernel.org
    [...]
    正在检查所有消息上的证明，可能需要片刻...
---
      ✓ [PATCH v1 1/3] kselftest/arm64: Correct buffer allocation for SVE Z registers
      ✓ [PATCH v1 2/3] arm64/sve: Document our actual ABI for clearing registers on syscall
      ✓ [PATCH v1 3/3] kselftest/arm64: Enforce actual ABI for SVE syscalls
      ---
      ✓ 签名: openpgp/broonie@kernel.org
      ✓ 签名: DKIM/kernel.org

.. note::

    Patatt和b4仍在积极开发中，你应该检查这些项目的最新文档，了解任何新功能或更新。
.. _kernel_identities:

如何验证内核开发者的身份
======================

签署标签和提交很容易，但如何验证用于签署某些内容的密钥属于实际的内核开发者而非恶意冒充者？

使用WKD和DANE配置自动密钥检索
---------------------------------

如果你不是一个拥有大量其他开发者公钥的人，那么可以通过依赖密钥自动发现和自动检索来启动你的密钥环。GnuPG可以借助其他委派信任技术，即DNSSEC和TLS，帮助你开始，如果你觉得从零开始建立自己的信任网络太过艰巨的话。
向你的``~/.gnupg/gpg.conf``中添加以下内容：

    auto-key-locate wkd,dane,local
    auto-key-retrieve

DNS-Based Authentication of Named Entities ("DANE")是一种在DNS中发布公钥并使用DNSSEC签名区域对其进行安全保护的方法。Web Key Directory ("WKD")是另一种使用HTTPS查找达到相同目的的方法。当使用DANE或WKD查找公钥时，GnuPG将在将自动检索的公钥添加到你的本地密钥环之前验证DNSSEC或TLS证书。
Kernel.org为所有拥有kernel.org账户的开发者发布了WKD。一旦你在``gpg.conf``中做了上述更改，你可以自动检索Linus Torvalds和Greg Kroah-Hartman的密钥（如果你还没有它们）：

    $ gpg --locate-keys torvalds@kernel.org gregkh@kernel.org

如果你有kernel.org账户，那么你应该`将kernel.org UID添加到你的密钥`_以使WKD对其他内核开发者更有用。
.. _`将kernel.org UID添加到你的密钥`: https://korg.wiki.kernel.org/userdoc/mail#adding_a_kernelorg_uid_to_your_pgp_key

信任网络(WOT)与首次使用信任(TOFU)
-------------------------------------

PGP包含一种称为“信任网络”的信任委派机制。从根本上说，这是试图替代HTTPS/TLS世界的集中式认证机构的需求。与各种软件制造商指定谁应该是你的可信认证实体不同，PGP将这一责任留给每个用户。
不幸的是，很少有人了解信任网络（Web of Trust）的工作原理。尽管它仍然是OpenPGP规范中的一个重要方面，GnuPG的较新版本（2.2及以上）已经实现了一种替代机制，称为“首次使用时的信任”（TOFU）。你可以将TOFU视为“类似SSH的信任方式”。在SSH中，当你第一次连接到远程系统时，其密钥指纹会被记录并记住。如果未来的某个时刻密钥发生了变化，SSH客户端会向你发出警告并且拒绝连接，迫使你决定是否信任更改后的密钥。同样地，在你第一次导入某人的PGP密钥时，默认假设它是有效的。如果在未来任何时候GnuPG遇到另一个具有相同身份的密钥，那么之前导入的密钥和新的密钥都会被标记为无效，你需要手动确定保留哪一个。

我们建议你使用结合TOFU+PGP的信任模型（这是GnuPG v2的新默认设置）。要设置它，请在`~/.gnupg/gpg.conf`中添加（或修改）`trust-model`设置：

    trust-model tofu+pgp

使用kernel.org的信任网络仓库
------------------------------

kernel.org维护了一个包含开发人员公钥的git仓库，作为过去几年几乎消失的密钥服务器网络的一种替代方案。关于如何将该仓库设置为你的公钥来源的完整文档可以在这里找到：

- [Kernel开发者PGP密钥环]_

如果你是一名内核开发者，请考虑提交你的密钥以供纳入该密钥环。
.. _[Kernel开发者PGP密钥环]: https://korg.docs.kernel.org/pgpkeys.html
