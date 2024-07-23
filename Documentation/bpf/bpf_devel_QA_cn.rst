如何与BPF子系统交互
====================

本文件提供了关于报告错误、提交补丁以及为稳定内核排队补丁的各种工作流程的BPF子系统信息。对于提交补丁的一般信息，请参阅`Documentation/process/submitting-patches.rst`。本文档仅描述与BPF相关的额外具体事项。
.. contents::
    :local:
    :depth: 2

报告错误
=========

问：我如何报告BPF内核代码的错误？
-----------------------------------
答：由于所有BPF内核开发以及bpftool和iproute2 BPF加载器开发都是通过bpf内核邮件列表进行的，请将发现的所有与BPF相关的问题报告到以下邮件列表：

 bpf@vger.kernel.org

这可能也包括与XDP、BPF追踪等有关的问题
鉴于netdev的流量很大，请在抄送中添加BPF维护者（来自内核的`MAINTAINERS`文件）：

* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

如果已确定了导致问题的提交，确保在报告中也将实际的提交作者加入抄送。他们通常可以通过内核的git树识别出来
**请不要向bugzilla.kernel.org报告BPF问题，因为可以肯定的是，报告的问题会被忽视。**

提交补丁
========

问：在我发送补丁以供审核之前，如何运行BPF持续集成(CI)？
-----------------------------------------------------
答：BPF CI基于GitHub并托管在https://github.com/kernel-patches/bpf。虽然GitHub还提供了一个命令行界面(CLI)，可用于实现相同的结果，但此处我们关注基于用户界面(UI)的工作流
以下步骤说明了如何为你的补丁启动CI运行：

- 在你自己的账户下创建上述仓库的一个分支（一次性操作）

- 本地克隆该分支，检查出一个新的分支，跟踪bpf-next或bpf分支，并在此基础上应用你待测试的补丁

- 将本地分支推送到你的分支，并针对kernel-patches/bpf的bpf-next_base或bpf_base分支创建一个拉取请求

在创建拉取请求后不久，CI工作流将开始运行。请注意，容量与提交上游的补丁检查共享，因此根据使用情况，运行可能需要一段时间才能完成
此外需要注意的是，两个基线分支（bpf-next_base和bpf_base）将在所跟踪的上游分支上推送补丁时更新。因此，你的补丁集也会自动尝试重新定位
这种行为可能导致CI运行被中止，并在新的基线上重新启动
问：我需要将我的BPF补丁提交到哪个邮件列表？
-------------------------------------------------
答：请将你的BPF补丁提交到bpf内核邮件列表：

 bpf@vger.kernel.org

如果你的补丁在不同的子系统中有更改（例如
翻译为中文：

(如网络，追踪，安全等)，请确保抄送给相关的内核邮件列表和维护者，以便他们能够审查更改并为补丁提供他们的认可（Acked-by）。

问：我可以在哪里找到当前正在讨论的BPF子系统的补丁？
-------------------------------------------------------------------------
答：所有抄送给netdev的补丁都会在netdev的补丁工作项目下排队等待审查：

  https://patchwork.kernel.org/project/netdevbpf/list/

那些针对BPF的补丁会被分配给一个'bpf'委托人，由BPF维护者进行进一步处理。当前正在审查的补丁队列可以在这里找到：

  https://patchwork.kernel.org/project/netdevbpf/list/?delegate=121173

一旦补丁被整个BPF社区审查并通过BPF维护者的批准，其在补丁工作中的状态将更改为“已接受”，提交者将通过邮件收到通知。这意味着从BPF的角度看，补丁看起来很好，并且已经被应用到两个BPF内核树之一。
如果社区的反馈要求对补丁进行重制，其在补丁工作中的状态将设置为“请求更改”，并从当前的审查队列中清除。同样，对于那些可能被拒绝或不适用于BPF树（但分配给了'bpf'委托人）的补丁也是如此。

问：这些更改如何进入Linux？
------------------------------------------------
答：有两个BPF内核树（Git仓库）。一旦补丁被BPF维护者接受，它们将被应用到两个BPF树之一：

 * https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf.git/
 * https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/

bpf树本身仅用于修复，而bpf-next则用于功能，清理或其他类型的改进（“类似next”的内容）。这类似于网络的net和net-next树。bpf和bpf-next都只有一个主分支，以简化补丁应该基于哪个分支进行重新构建的问题。
bpf树中积累的BPF补丁将定期被拉入net内核树。同样，被接受进入bpf-next树的BPF补丁将进入net-next树。net和net-next均由David S. Miller管理。从那里，它们将进入由Linus Torvalds管理的内核主线树。要了解net和net-next合并到主线树的过程，请参阅netdev子系统文档：
Documentation/process/maintainer-netdev.rst
偶尔，为了避免合并冲突，我们可能会向其他树（例如追踪）发送包含少量补丁的拉取请求，但是net和net-next始终是集成的主要目标树。
拉取请求将包含累积补丁的高级摘要，可以通过以下主题行在netdev内核邮件列表中进行搜索（``yyyy-mm-dd``是拉取请求的日期）：

  拉取请求：bpf yyyy-mm-dd
  拉取请求：bpf-next yyyy-mm-dd

问：我如何表明我的补丁应应用于哪个树（bpf与bpf-next）？
---------------------------------------------------------------------------------
答：该过程与netdev子系统文档中描述的完全相同，位于Documentation/process/maintainer-netdev.rst，
因此请阅读。主题行必须表明补丁是修复还是“类似next”的内容，以便让维护者知道它是否针对bpf或bpf-next
对于最终将在bpf -> net树中落地的修复，主题必须如下所示：

  git format-patch --subject-prefix='PATCH bpf' start..finish

对于应最终在bpf-next -> net-next落地的功能/改进等，主题必须如下所示：

  git format-patch --subject-prefix='PATCH bpf-next' start..finish

如果不确定补丁或补丁系列是否应该直接进入bpf或net，或者直接进入bpf-next或net-next，即使主题行表示net或net-next为目标也没问题
最终，由维护者来完成补丁的委派
如果明确补丁应该进入bpf或bpf-next树，请确保将补丁针对那些树进行重新构建，以减少潜在的冲突。
如果补丁或补丁系列需要重做并再次以第二版或后续版本的形式发出，也要求在主题前缀中添加版本号（如`v2`、`v3`等）：

```
git format-patch --subject-prefix='PATCH bpf-next v2' start..finish
```

当补丁系列被要求进行修改时，应将整个补丁系列连同反馈一起重新发送（永远不要在旧系列的基础上单独发送差异文件）

问：补丁应用到bpf或bpf-next树意味着什么？
答：这意味着从BPF的角度看，该补丁适合主线内核的合并。
请注意，这并不意味着补丁会自动最终被net或net-next树接受：

在bpf内核邮件列表上，审查可能随时进行。如果围绕一个补丁的讨论得出结论认为它不能按原样被包含，我们将要么应用后续修复，要么完全从树中删除它们。因此，我们保留必要时重新构建树的权利。毕竟，树的目的在于：

i) 汇总并准备BPF补丁，以便集成到net和net-next这样的树中；

ii) 在补丁进一步推进之前，在这些补丁上运行广泛的BPF测试套件和工作负载。

一旦BPF拉取请求被David S. Miller接受，那么补丁将分别进入net或net-next树，并从那里进一步进入主线内核。再次参考netdev子系统的文档，位于`Documentation/process/maintainer-netdev.rst`，获取有关它们多久与主线合并的额外信息。

问：我需要等待多长时间才能收到我的BPF补丁的反馈？
答：我们努力保持低延迟。通常的反馈时间大约是2到3个工作日。这可能根据变化的复杂性和当前的补丁负载而有所不同。

问：你多久向像net或net-next这样的主要内核树发送拉取请求？
答：拉取请求会频繁发送，以免在bpf或bpf-next中积累过多补丁。
大致来说，每周末可以期待每个树的定期拉取请求。在某些情况下，根据当前的补丁负载或紧迫性，拉取请求也可能在周中出现。

问：当合并窗口开放时，补丁是否会被应用到bpf-next？
答：当合并窗口开放时，不会处理bpf-next。
这大致相当于net-next补丁的处理方式，因此可以自由阅读netdev文档`Documentation/process/maintainer-netdev.rst`中的更多细节。
在这两周的合并窗口期间，我们可能会要求你在bpf-next再次开放后重新发送你的补丁系列。一旦Linus在合并窗口结束后发布了`v*-rc1`，我们将继续处理bpf-next。

对于没有订阅内核邮件列表的人来说，David S. Miller运行了一个状态页面，提供了关于net-next的指导：

```
http://vger.kernel.org/~davem/net-next.html
```

问：验证器变更与测试用例
问：我对BPF验证器进行了更改，我需要为BPF内核自测添加测试用例吗？

答：如果补丁改变了验证器的行为，则确实需要向BPF内核自测套件添加测试用例。如果缺少这些测试用例且我们认为需要它们，那么在接受任何更改之前，我们可能会要求提供这些测试用例。
特别地，test_verifier.c 跟踪了大量的 BPF 测试用例，包括许多受限的 C 代码可能生成的 LLVM BPF 后端角落案例。因此，增加测试用例是绝对关键的，以确保未来的更改不会意外影响先前的使用场景。因此，将这些测试用例视为：在 test_verifier.c 中未跟踪的验证器行为可能会潜在地改变。

Q: samples/bpf 与自测（selftests）的偏好？
--------------------------------------
Q: 我应该何时将代码添加到 `samples/bpf/`，何时添加到 BPF 内核自测_？

A: 一般来说，我们更倾向于将代码添加到 BPF 内核自测_而非 `samples/bpf/`。原因很简单：内核自测由各种机器人定期运行，用于测试内核回归。我们向 BPF 自测中添加的测试用例越多，覆盖范围就越广，意外破坏的可能性就越小。这并不是说 BPF 内核自测不能演示特定功能的使用方式。
也就是说，`samples/bpf/` 可能是人们开始学习的好地方，因此简单的功能演示可以放入 `samples/bpf/`，而高级功能性和角落案例测试则更适合放入内核自测中。
如果您的示例看起来像一个测试用例，那么选择 BPF 内核自测吧！

Q: 我何时应将代码添加到 bpftool？
------------------------------------
A: bpftool（位于 tools/bpf/bpftool/ 下）的主要目的是提供一个中心用户空间工具，用于调试和检查内核中活跃的 BPF 程序和映射。如果与 BPF 相关的 UAPI 更改允许转储程序或映射的额外信息，则也应扩展 bpftool 以支持转储它们。

Q: 我何时应将代码添加到 iproute2 的 BPF 加载器？
-----------------------------------------------------
A: 对于与 XDP 或 tc 层（例如 `cls_bpf`）相关的 UAPI 更改，惯例是将与控制路径相关的变化添加到 iproute2 的 BPF 加载器中，从用户空间角度出发。这不仅有助于确保 UAPI 更改被设计得可用，而且还能让这些变化对主要下游发行版的更广泛用户群体可用。

Q: 您是否接受 iproute2 的 BPF 加载器的补丁？
---------------------------------------------------
A: iproute2 的 BPF 加载器的补丁需要发送至：

  netdev@vger.kernel.org

虽然这些补丁不由 BPF 内核维护者处理，请同样抄送他们进行审核。
iproute2 的官方 Git 仓库由 Stephen Hemminger 运行，地址为：

  https://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git/

补丁的主题前缀必须为 '``[PATCH iproute2 master]``' 或 '``[PATCH iproute2 net-next]``'。'``master``' 或 '``net-next``' 描述了补丁应用的目标分支。也就是说，如果内核更改已进入 net-next 内核树，则相关的 iproute2 更改需进入 iproute2 的 net-next 分支；否则，它们可以针对 master 分支。iproute2 的 net-next 分支将在当前来自 master 的 iproute2 版本发布后合并到 master 分支。
如同 BPF，这些补丁最终会出现在 netdev 项目的 patchwork 中，并委托给 'shemminger' 进一步处理：

  http://patchwork.ozlabs.org/project/netdev/list/?delegate=389

Q: 在提交我的 BPF 补丁之前，最低要求是什么？
-------------------------------------------------
A: 提交补丁时，务必花时间并适当地测试您的补丁 *在提交之前*。不要急于求成！如果维护者发现您的补丁未经适当测试，这是让他们感到不满的好方法。测试补丁提交是硬性要求！

请注意，提交到 bpf 树的修复 *必须* 包含 ``Fixes:`` 标签。
同样的规则适用于针对 bpf-next 的修复，其中受影响的提交在 net-next（或某些情况下 bpf-next）中。``Fixes:`` 标签对于识别后续提交至关重要，并极大地帮助那些需要做回退的人，所以这是必须的！

我们也不接受空提交消息的补丁。请花时间编写高质量的提交消息，这是必不可少的！

这样思考：一个月后，其他开发人员查看您的代码时，需要理解 *为何* 以某种方式做出特定更改，以及原始作者的分析或假设是否存在缺陷。因此，提供适当的理由并描述更改的用例是必须的。
### 带有超过一个补丁的提交必须附带一封包含系列高级描述的封面信。这份高级概述将由BPF维护者放入合并提交中，以便将来可以从git日志中访问。

### Q: 改变BPF JIT和/或LLVM的功能
----------------------------------------

### Q: 添加新的指令或功能时，如果需要集成到BPF JIT和/或LLVM中，我需要注意什么？

A: 我们努力保持所有BPF JIT更新，以确保在不同架构上运行BPF程序时能获得相同的用户体验，而不会因为启用了内核中的BPF JIT而导致程序退回到效率较低的解释器。
如果你无法为某些架构实现或测试所需的JIT更改，请与相关的BPF JIT开发者合作，以及时完成该功能。
请参考git日志（`arch/*/net/`）来找到相关的人协助。
同时，对于新指令，务必添加BPF测试案例（例如`test_bpf.c`和`test_verifier.c`），以确保它们能够得到广泛的测试覆盖，并帮助运行时测试各种BPF JIT。
对于新的BPF指令，在变更被接受进入Linux内核后，请在LLVM的BPF后端中实现支持。更多详细信息请参阅下面的LLVM部分。

### 稳定版本提交
==================

### Q: 我需要在稳定版本内核中使用一个特定的BPF提交。我应该怎么做？
--------------------------------------------------------------------

A: 如果你需要在稳定版本内核中使用一个特定的修复，请首先检查该提交是否已经应用到了相关的`linux-*.y`分支：

  https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git/

如果没有，则向BPF维护者发送邮件，并抄送netdev内核邮件列表，请求将此修复排队处理：

  netdev@vger.kernel.org

一般流程与netdev相同，更多信息请参阅网络子系统的文档：
Documentation/process/maintainer-netdev.rst

### Q: 是否也回溯到当前未作为稳定版本维护的内核？
----------------------------------------------------------------------

A: 不会。如果你需要在当前未被稳定维护者维护的内核中使用一个特定的BPF提交，那么你需要自行处理。
当前稳定版本和长期稳定版本的内核都在这里列出：

  https://www.kernel.org/

### Q: 我即将提交的BPF补丁也需要在稳定版本中应用
-------------------------------------------------------------------

我应该怎么做？

A: 这与一般的netdev补丁提交规则相同，详情请参阅netdev文档：
Documentation/process/maintainer-netdev.rst
不要在补丁描述中添加“`Cc: stable@vger.kernel.org`”，而是请求BPF维护者进行排队处理。这可以通过在补丁的“---”部分下写一个备注来实现，这部分内容不会进入git日志。或者，你也可以通过简单的邮件请求来实现。
问：队列稳定补丁
-----------------------
问：我在哪里可以找到当前排队的BPF补丁，这些补丁将被提交到稳定版本？

答：一旦修复关键错误的补丁被应用到bpf树中，它们就会在以下位置排队等待稳定提交：

  http://patchwork.ozlabs.org/bundle/bpf/stable/?state=*

在那里，它们至少会等到相关的提交进入主线内核树。
经过更广泛的曝光后，排队的补丁将由BPF维护者提交给稳定维护者。

测试补丁
===============

问：如何运行BPF自测
---------------------------
答：在你使用新编译的内核启动后，导航到BPF自测_套件以测试BPF功能（当前工作目录指向克隆的git树的根）::

  $ cd tools/testing/selftests/bpf/
  $ make

要运行验证器测试，请执行以下操作::

  $ sudo ./test_verifier

验证器测试会打印出所有正在进行的检查。
在运行所有测试后，总结将输出测试成功和失败的信息::

  总结：418通过，0失败

为了运行所有BPF自测，需要以下命令::

  $ sudo make run_tests

详细信息请参阅：doc:`内核自测文档 </dev-tools/kselftest>`
为了使尽可能多的测试通过，测试内核的.config应尽可能与
tools/testing/selftests/bpf中的配置文件片段相匹配
最后，为了确保支持最新的BPF类型格式特性——
在Documentation/bpf/btf.rst中讨论——对于使用CONFIG_DEBUG_INFO_BTF=y构建的内核，
需要pahole版本1.16
pahole包含在dwarves包中，或者可以从源代码构建

https://github.com/acmel/dwarves

自从提交21507cd3e97b("pahole: 在lib/bpf下添加libbpf作为子模块")之后，从v1.13开始，
pahole开始使用libbpf定义和API
它与git仓库配合良好，因为libbpf子模块将使用"git submodule update --init --recursive"进行更新
不幸的是，默认的github发布源代码不包含libbpf子模块源代码，这将导致构建问题，
从https://git.kernel.org/pub/scm/devel/pahole/pahole.git/获取的tarball与github相同，
你可以从以下位置获得带有相应libbpf子模块代码的源tarball

https://fedorapeople.org/~acme/dwarves

一些发行版已经打包了pahole版本1.16，例如Fedora，Gentoo

问：我应该让我的内核运行哪个BPF内核自测版本？
---------------------------------------------------------------------
答：如果你运行的是内核“xyz”，那么总是运行来自该内核“xyz”的BPF内核自测。
不要期望来自最新主线树的BPF自测会一直通过。
特别是在test_bpf.c和test_verifier.c中，有大量的测试用例，并且会持续更新新的BPF测试序列，或者根据验证器的变化（例如，由于验证器变得更智能，能够更好地追踪某些事项）来调整现有的测试用例。

LLVM
====

问：我在哪里可以找到支持BPF的LLVM？
-----------------------------------------
答：自版本3.7.1以来，LLVM的BPF后端已集成到上游的LLVM中。
如今所有主要的发行版都提供了带有启用BPF后端的LLVM，因此对于大多数使用场景来说，不再需要手动编译LLVM，只需安装发行版提供的软件包即可。
LLVM的静态编译器通过`llc --version`列出支持的目标，确保BPF目标被列出。示例如下：

     $ llc --version
     LLVM (http://llvm.org/):
       LLVM 版本 10.0.0
       最优构建
默认目标：x86_64-unknown-linux-gnu
       主机CPU：skylake

       已注册的目标：
         aarch64    - AArch64（小端）
         bpf        - BPF（主机字节序）
         bpfeb      - BPF（大端）
         bpfel      - BPF（小端）
         x86        - 32位X86：Pentium-Pro及更高版本
         x86-64     - 64位X86：EM64T和AMD64

为了利用LLVM的BPF后端最新添加的功能，开发人员建议运行最新的LLVM版本。对新BPF内核功能的支持，如BPF指令集的增加，通常与LLVM的开发同步进行。
所有LLVM的发布版本可以在以下网址找到：http://releases.llvm.org/

问：明白了，那我如何手动构建LLVM呢？
--------------------------------------------------
答：我们建议希望获得最快增量构建的开发人员使用Ninja构建系统，你可以在系统的包管理器中找到它，通常该包名为ninja或ninja-build。
你需要ninja、cmake和gcc-c++作为LLVM的构建需求。一旦你准备就绪，就可以从git仓库构建最新的LLVM和clang版本：

     $ git clone https://github.com/llvm/llvm-project.git
     $ mkdir -p llvm-project/llvm/build
     $ cd llvm-project/llvm/build
     $ cmake .. -G "Ninja" -DLLVM_TARGETS_TO_BUILD="BPF;X86" \
                -DLLVM_ENABLE_PROJECTS="clang"    \
                -DCMAKE_BUILD_TYPE=Release        \
                -DLLVM_BUILD_RUNTIME=OFF
     $ ninja

构建的二进制文件随后可以在build/bin/目录下找到，你可以将PATH变量指向这里。
将``-DLLVM_TARGETS_TO_BUILD``设置为你想要构建的目标，你可以在llvm-project/llvm/lib/Target目录下找到完整的目标列表。

问：报告LLVM的BPF问题
----------------------------
问：我是否应该向BPF内核维护者报告LLVM的BPF代码生成后端的问题，或者报告验证器拒绝接受的由LLVM生成的代码？

答：是的，请这样做！

LLVM的BPF后端是整个BPF基础设施的关键组成部分，它与内核侧程序的验证紧密相关。因此，任何一方的问题都需要调查并在必要时修复。
因此，请确保在netdev内核邮件列表上提出这些问题，并抄送给LLVM和内核部分的BPF维护者：

* Yonghong Song <yhs@fb.com>
* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

LLVM也有一个问题跟踪器，其中可以找到与BPF相关的错误：

  https://bugs.llvm.org/buglist.cgi?quicksearch=bpf

但是，最好通过邮件列表联系维护者。
问题：如何将新的BPF指令集成到内核和LLVM中？
------------------------------------------------
问：我已经向内核添加了一个新的BPF指令，怎样才能将其整合到LLVM中？

答：LLVM的BPF后端有一个`-mcpu`选择器，用于允许选择BPF指令集扩展。默认情况下，使用的是`generic`处理器目标，这是BPF的基本指令集（v1）。
LLVM有一个选项可以选择`-mcpu=probe`，它会探测主机内核支持的BPF指令集扩展，并自动选择最优集合。
对于交叉编译，也可以手动选择特定版本:: 

     $ llc -march bpf -mcpu=help
     适用于此目标的CPU：

       generic - 选择通用处理器
probe   - 选择探测处理器
v1      - 选择v1处理器
v2      - 选择v2处理器
[...]

向Linux内核新增加的BPF指令需要遵循相同的方案，提升指令集版本，并实现对扩展的探测，以便使用`-mcpu=probe`的用户在升级他们的内核时可以透明地从优化中获益。
如果你无法为新添加的BPF指令实现支持，请联系BPF开发者寻求帮助。
顺便说一下，BPF内核自测是使用`-mcpu=probe`运行的，以获得更好的测试覆盖率。

问题：针对bpf的目标的clang标志是什么？
--------------------------------------------
问：在某些情况下使用了clang标志`--target=bpf`，但在其他情况下则使用默认的clang目标，该目标与底层架构相匹配。
LLVM IR生成和优化尝试保持架构无关性，但`--target=<arch>`仍然对生成的代码产生一定影响：

- BPF程序可能递归包含带有文件作用域内联汇编代码的头文件。默认目标可以很好地处理这种情况，而`bpf`目标在BPF后端汇编器不理解这些汇编代码时可能会失败，这在大多数情况下是真实的。
- 当不使用`-g`编译时，额外的elf节，例如`.eh_frame`和`.rela.eh_frame`，可能会出现在默认目标的对象文件中，但在`bpf`目标中则不会出现。
- 默认目标可能会将C语言的switch语句转换为switch表查找和跳转操作。由于switch表位于全局只读区域，BPF程序在加载时会失败。`bpf`目标不支持switch表优化。Clang选项`-fno-jump-tables`可用于禁用switch表生成。
- 对于Clang的`--target=bpf`，可以保证指针或long/unsigned long类型始终具有64位宽度，无论底层Clang二进制文件、默认目标（或内核）是否为32位。然而，当使用本机Clang目标时，它将根据底层架构的约定编译这些类型，这意味着在32位架构下，BPF上下文结构中的指针或long/unsigned long类型将具有32位宽度，而BPF LLVM后端仍以64位运行。本机目标主要用于追踪中，如遍历`pt_regs`或其他内核结构，其中CPU寄存器宽度很重要。
除此之外，一般推荐使用`clang --target=bpf`。

你应该在以下情况下使用默认目标：

- 你的程序包含了如`ptrace.h`这样的头文件，最终会引入包含文件作用域主机汇编代码的某些头文件。
- 你可以添加`-fno-jump-tables`来解决switch表问题。
否则，你可以使用`bpf`目标。此外，你**必须**在以下情况下使用`bpf`目标：

- 你的程序使用了带有指针或long/unsigned long类型的与BPF助手或上下文数据结构接口的数据结构。对这些结构的访问由BPF验证器进行验证，并且如果本机架构与BPF架构（例如64位）不一致，可能会导致验证失败。一个例子是BPF_PROG_TYPE_SK_MSG需要`--target=bpf`。

.. 链接
.. _selftests:
   https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/

祝你BPF编程愉快！
