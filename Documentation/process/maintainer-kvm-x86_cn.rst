SPDX 许可证标识符: GPL-2.0

KVM x86
=======

前言
--------
KVM 努力成为一个包容的社区；我们珍视并鼓励新成员的贡献。请不要因为本文档的长度及其包含的众多规则/指导方针而感到气馁或害怕。每个人都会犯错误，每个人都有过新手阶段。只要你真诚地努力遵循 KVM x86 的指导方针，乐于接受反馈，并从自己的错误中学习，你将会受到热情的欢迎，而不是遭到排斥。
简而言之
-----
测试是必须的。与既有的风格和模式保持一致。
代码库
-----
目前 KVM x86 正处于一个过渡期，从作为主要 KVM 代码库的一部分转变为“仅仅是另一个 KVM 架构”。因此，KVM x86 被分散在主要的 KVM 代码库 `git.kernel.org/pub/scm/virt/kvm/kvm.git` 和专门针对 KVM x86 的代码库 `github.com/kvm-x86/linux.git` 中。
通常来说，当前周期的修复直接应用于主要的 KVM 代码库，而所有针对下一个周期的开发都通过 KVM x86 代码库进行。如果极少数情况下，当前周期的修复通过 KVM x86 代码库处理，它将首先应用到 `fixes` 分支，然后再进入主要的 KVM 代码库。
需要注意的是，这个过渡期预计将持续很长时间，即在可预见的未来内将是常态。
分支
~~~~~~~~
KVM x86 代码库被组织成多个主题分支。使用更细粒度的主题分支的目的是为了更容易关注某个领域的开发，并且限制人为错误和/或有缺陷提交所带来的附带损害，例如删除一个主题分支的最新提交不会影响其他正在进行中的提交的 SHA1 哈希值，而且由于发现 bug 而拒绝一个拉取请求只会延迟那个特定主题分支的进展。
除了 `next` 和 `fixes` 分支之外的所有主题分支，都是按需通过克苏鲁合并（Cthulhu merge）方式合并进 `next` 分支的，即当一个主题分支更新时。
因此，对 `next` 分支的强制推送很常见。
生命周期
~~~~~~~~~
针对当前发布的修复，也就是主线版本，通常直接应用于主要的 KVM 代码库，即不通过 KVM x86 代码库。
针对下一个发布的变更则通过 KVM x86 代码库进行。每个 KVM x86 主题分支的拉取请求（从 KVM x86 到主要 KVM）通常会在林纳斯打开合并窗口的一周前发出，例如对于常规发布，在 rc7 后的一周。如果一切顺利，这些主题分支将被合并进在林纳斯的合并窗口期间发送的主要 KVM 拉取请求中。
KVM x86树没有自己的官方合并窗口，但在rc5左右对新功能有一个非正式的关闭时间点，在rc6左右对修复（针对下一个版本发布；有关当前版本发布的修复请参见上述内容）也有一个非正式的关闭时间点。

时间表
------
提交通常按照先进先出（FIFO）的顺序进行审查和应用，对于系列的大小、"热点缓存"的补丁等有一些灵活的空间。修复，特别是针对当前版本或稳定分支的修复可以优先处理。
那些将通过非KVM树（最常见的是通过tip树）进行处理和/或其他获得确认/审查的补丁也在一定程度上享有优先权。
需要注意的是，绝大多数的审查工作是在rc1到rc6之间完成的，前后略有浮动。
从rc6到下一个rc1之间的这段时间用于处理其他任务，即在这段时间内保持无线电静默并不罕见。
欢迎发送消息以获取状态更新，但请记住当前版本周期的时间，并且要有合理的期望值。如果您请求接受，而不仅仅是寻求反馈或更新，请确保您的补丁已准备好合并！对于破坏构建或测试失败的系列发送的消息会导致维护者不高兴！

开发
----

基础树/分支
~~~~~~~~~~~
针对当前版本（也称为主线）的修复应该基于`git://git.kernel.org/pub/scm/virt/kvm/kvm.git master`。请注意，修复并不自动保证被包含在当前版本中。虽然没有单一规则，但通常只有紧急、关键的bug修复以及在当前版本中引入的问题修复才应针对当前版本。
其他所有内容都应该基于`kvm-x86/next`，即无需选择特定的主题分支作为基础。如果有跨主题分支的冲突和/或依赖关系，则由维护者负责解决这些问题。
使用`kvm-x86/next`作为基础的唯一例外是当补丁/系列为多架构系列时，即对通用KVM代码有非微不足道的修改和/或其他架构代码有超出表面的更改。多架构补丁/系列应基于KVM历史上的一个共同、稳定的点，例如`kvm-x86 next`所基于的发布候选版本。如果您不确定某个补丁/系列是否真正属于多架构类别，请谨慎行事并将其视为多架构，即使用一个共同的基础。

编码风格
~~~~~~~~~
在风格、命名、模式等方面，一致性是KVM x86中的首要原则。如果无法匹配现有风格，那么就尽量与已有的代码保持一致。
除了下面列出的一些例外情况外，请遵循tip树维护者偏好的:ref:`maintainer-tip-coding-style`，因为补丁/系列经常同时涉及KVM和非KVM x86文件，即会吸引KVM和tip树维护者的注意。
使用反向圣诞树（也称为反向圣诞节树或反向XMAS树）进行变量声明并非严格要求，尽管仍推荐这样做。除了一些特殊情况之外，请勿对函数使用内核文档注释。绝大多数所谓的“公共”KVM函数实际上并不是真正公开的，因为它们仅用于KVM内部使用（有计划将KVM的头文件和导出私有化以实施这一点）。

注释
~~~~~
使用祈使语气编写注释，并避免使用代词。使用注释来提供代码的高层次概述，或者解释代码为何如此工作。不要重复代码字面上做的事情；让代码自己说话。如果代码本身难以理解，注释也无法帮助。

SDM和APM参考
~~~~~~~~~~~~~~
KVM的大量代码库直接与Intel的软件开发手册(SDM)和AMD的架构程序员手册(APM)中定义的架构行为相关。在没有额外上下文的情况下使用“Intel的SDM”、“AMD的APM”，甚至仅仅使用“SDM”或“APM”是完全可接受的。

不要按数字引用特定的部分、表格、图表等，尤其是在注释中。相反，如果必要（见下文），复制相关的片段并按名称引用部分/表格/图表。SDM和APM的布局不断变化，因此编号/标签并不稳定。

通常来说，在注释中不要明确引用或从SDM或APM中复制粘贴。除了少数例外，KVM必须遵循架构行为，因此可以推断KVM的行为是在模拟SDM和/或APM的行为。

注意：在更改日志中引用SDM/APM以证明更改并提供背景信息是完全可以的，并且被鼓励。

简短日志
~~~~~~~~~
首选的前缀格式是`KVM: <主题>:`，其中`<主题>`是以下内容之一：

  - x86
  - x86/mmu
  - x86/pmu
  - x86/xen
  - 自我测试(selftests)
  - SVM
  - nSVM
  - VMX
  - nVMX

**不要使用x86/kvm！** `x86/kvm`专门用于Linux作为KVM客户机的变化，即用于arch/x86/kernel/kvm.c。不要使用文件名或完整的文件路径作为主题/简短日志的前缀。

注意，这些与主题分支并不一致（主题分支更关心代码冲突）。

所有名称都是大小写敏感的！`KVM: x86:` 是好的，而`kvm: vmx:`则不是。
首字母大写凝练的补丁描述中的第一个单词，但省略结尾的标点符号。例如：

    KVM: x86: 修复 function_xyz() 中的空指针解引用

而不是：

    kvm: x86: 修复 function_xyz 中的空指针解引用
如果一个补丁涉及多个主题，请沿着概念树向上找到第一个共同的父级（通常是“x86”）。当不确定时，“`git log path/to/file`”应该能提供合理的提示。
新主题偶尔会出现，但如果想要引入新主题，请先在列表上发起讨论，即不要擅自行动。
更多信息请参见 :ref:`the_canonical_patch_format`，有一点修正：不要将70-75个字符作为绝对严格的限制。相反，将75个字符视为坚定但非硬性的限制，并将80个字符作为硬性限制。也就是说，如果有充分的理由，可以让变更日志稍微超过标准限制。

**变更日志**
最重要的是，使用祈使句来撰写变更日志并避免使用代词。更多信息请参见 :ref:`describe_changes`，有一点修正：首先简要说明实际的变化，然后给出上下文和背景信息。注意！这个顺序直接与尖端树(preferred approach)推荐的方法冲突！当发送主要针对非KVM代码的arch/x86代码的补丁时，请遵循尖端树的推荐风格。
在KVM x86中，更倾向于先说明补丁做了什么再进入细节，原因有几个。首要的是，实际上修改了哪些代码可以认为是最重要的信息，因此这些信息应该易于查找。将“实际的变化”埋藏在三段以上的背景信息之后的一行文字中，使得这些信息很难被发现。
对于初次审查，可以争论“哪里出了问题”可能更重要，但对于浏览日志和git考古学来说，细节变得越来越不重要。例如，在一系列“git blame”的过程中，沿途每个变化的细节都是无用的，只有导致问题的根源的细节才是重要的。提供“做了什么改变”可以使人们快速确定一个提交是否可能感兴趣。
另一个先说明“做了什么改变”的好处是，几乎总是可以用一句话来说明“做了什么改变”。相反，除了最简单的bug之外，完全描述问题通常需要多句话或多段落。如果“做了什么改变”和“问题是什么”都非常简短，则顺序并不重要。但如果其中一个较短（几乎总是“做了什么改变”较短），那么先涵盖较短的部分是有利的，因为这对于有严格顺序偏好的读者/审阅者来说不太麻烦。例如，跳过一句话以获取上下文比跳过三段落以获取“做了什么改变”带来的不便要小得多。
### 修复

如果变更修复了 KVM/内核的 bug，即使该变更不需要回退到稳定版本的内核，或者修复的是旧版本中的 bug，也应添加 `Fixes:` 标签。

反之，如果确实需要回退，则应在补丁上明确标记 `"Cc: stable@vger.kernel"`（尽管邮件本身不必抄送 `stable`）；默认情况下，KVM x86 不参与回退修复。一些自动选择的补丁会得到回退，但需要显式的维护者批准（搜索 MANUALSEL）。

### 函数引用

当在注释、更改日志或简短日志（或任何地方）提及一个函数时，使用格式 `function_name()`。括号提供了上下文并消除了歧义。

### 测试

至少，系列中的所有补丁都必须在设置 `KVM_INTEL=m`、`KVM_AMD=m` 和 `KVM_WERROR=y` 的情况下干净地构建。构建所有可能的 Kconfig 组合并不现实，但越多越好。特别关注 `KVM_SMM`、`KVM_XEN`、`PROVE_LOCKING` 和 `X86_64` 这些配置项。

运行 KVM 自我测试和 KVM 单元测试也是强制性的（显然，测试必须通过）。唯一例外是那些对运行时行为影响微乎其微的变更，例如仅修改注释的补丁。尽可能且相关的情况下，在 Intel 和 AMD 上进行测试是非常推荐的。鼓励启动实际的虚拟机，但不是强制要求。

对于触及 KVM 阴影分页代码的变更，必须禁用 TDP（EPT/NPT）。对于影响通用 KVM MMU 代码的变更，强烈建议禁用 TDP。对于其他所有的变更，如果被修改的代码依赖于或与模块参数交互，那么必须使用相关设置进行测试。

请注意，KVM 自我测试和 KVM 单元测试已知存在失败情况。如果你怀疑失败不是由于你的变更引起的，请验证在有无你的变更时发生的是完全相同的失败。

触及 reStructuredText 文档（即 .rst 文件）的变更必须能够干净地构建 htmldocs，也就是说没有新的警告或错误。

如果你无法完全测试某个变更（例如因为缺乏硬件），请明确说明你能够进行的测试级别，例如在封面信中说明。

### 新特性

除一种例外情况外，新特性必须带有测试覆盖。虽然不一定需要 KVM 特定的测试（例如，如果通过运行足够启用的来宾虚拟机或在虚拟机中运行相关的内核自我测试来提供覆盖），但在所有情况下首选专用的 KVM 测试。特别是对于新硬件特性的启用，负面测试案例是强制性的，因为错误和异常流程很少仅仅通过运行虚拟机来测试。
### 唯一的例外

此规则的唯一例外是，如果KVM仅通过KVM_GET_SUPPORTED_CPUID宣传对某个功能的支持，即对于KVM无法阻止客户机使用且不存在真正启用机制的指令/特性。请注意，“新特性”并不仅仅意味着“新硬件特性”！那些无法很好地利用现有的KVM自测或KVM单元测试进行验证的新特性必须附带测试。

在没有测试的情况下发布新特性的开发以获取早期反馈是非常受欢迎的，但此类提交应该标记为RFC，并且在封面信中应清楚说明所请求/期望的是哪种类型的反馈。不要滥用RFC流程；RFC通常不会收到深入审查。

### 修复错误

除了那些显而易见、通过检查就能发现的错误之外，修复必须附带可以重现该问题的方法。在许多情况下，重现方法是隐含的，例如构建错误和测试失败，但读者仍然需要清楚哪里出了问题以及如何验证修复结果。对于通过非公开的工作负载或测试发现的错误，可以稍微放宽要求，但是强烈建议为此类错误提供回归测试。

一般来说，对于那些不容易重现的错误，我们更倾向于使用回归测试。即使错误最初是由诸如syzkaller之类的模糊测试工具发现的，如果该错误需要触发一种百万分之一级别的竞态条件，那么一个针对性的回归测试可能是必要的。

请注意，KVM中的错误很少既紧急又难以重现。在没有提供可以重现问题的方法之前，请先问问自己这个错误是否真的到了世界末日的地步。

### 发布

#### 链接

不要通过`In-Reply-To:`头部明确引用错误报告、补丁/系列的先前版本等。对于大型系列或者当版本号变得很高时，使用`In-Reply-To:`会变得一团糟，而且对于没有原始消息的人来说（比如某人没有被抄送错误报告，或者收件人列表在不同版本间发生变化），`In-Reply-To:`是没有用处的。

为了链接到错误报告、先前版本或任何感兴趣的内容，请使用lore链接。一般而言，在更改日志中不要包含指向先前版本的Link:，因为没有必要在git历史记录中记录这些信息（即将链接放在封面信或git忽略的部分）。对于导致产生补丁的错误报告和/或讨论，请提供正式的Link:。为什么做出这种改变的背景信息对于未来的读者来说非常有价值。
### Git 基础

如果你使用的是 Git 2.9.0 或更高版本（Google 的同事们，这适用于你们所有人！），请使用 `git format-patch` 命令，并带上 `--base` 标志来自动在生成的补丁中包含基树信息。

注意：只有当一个分支的上游被设置为其基础主题分支时，`--base=auto` 才能按预期工作，例如，如果您的上游被设置为个人备份仓库，则可能会产生错误的结果。另一种“自动”解决方案是根据开发分支的 KVM x86 主题来命名你的开发分支，并将这些名称传递给 `--base`。例如，可以命名为 `x86/pmu/my_branch_name`，然后编写一个小脚本来从当前分支名称中提取 `pmu`，从而得到 `--base=x/pmu`，其中 `x` 是您的仓库用来跟踪 KVM x86 远程分支的名称。

### 协同提交测试

与 KVM 变更相关的 KVM 自测（例如针对 bug 修复的回归测试）应作为一个系列与 KVM 变更一起提交。遵循内核的标准二分法规则，即导致测试失败的 KVM 变更应排在自测更新之后，反之，由于 KVM bug 导致失败的新测试应排在 KVM 修复之后。

KVM 单元测试 *必须* 单独提交。工具（如 b4 am）不知道 KVM 单元测试是一个单独的仓库，在一系列补丁应用到不同的树上时会感到困惑。为了将 KVM 单元测试补丁与 KVM 补丁关联起来，首先提交 KVM 的变更，然后在 KVM 单元测试补丁中提供指向 KVM 补丁/系列的 lore 链接。

### 通知

当一个补丁/系列被正式接受后，将会向原始提交（对于多补丁系列则是封面信件）发送一封回复邮件作为通知。通知将包括树和主题分支，以及已应用补丁的提交 SHA1 值。

如果只有一部分补丁被应用，这将在通知中明确说明。除非另有声明，否则默认情况下，任何未被接受的系列中的补丁需要更多工作，并应在新版本中重新提交。

如果某个补丁在正式接受后被撤销，将向通知邮件发送回复解释撤销的原因及下一步行动。

### SHA1 稳定性

SHA1 在进入 Linus 的树之前并不能保证100%稳定！一旦发送了通知，一个 SHA1 通常就会变得稳定，但总会有意外发生。

大多数情况下，如果已应用补丁的 SHA1 发生变化，将会更新通知邮件。但在某些场景下，例如所有 KVM x86 分支都需要重置时，将不会给出个别通知。

### 漏洞

能够被来宾利用以攻击主机（内核或用户空间）或被嵌套虚拟机利用以攻击其宿主（L2 攻击 L1）的 bug 对 KVM 尤为重要。如果您怀疑某个 bug 可能导致逃逸、数据泄露等问题，请遵循 :ref:`securitybugs` 中的安全漏洞协议。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
