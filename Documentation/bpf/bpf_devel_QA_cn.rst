如何与BPF子系统交互
====================

本文档为BPF子系统提供了关于报告错误、提交补丁以及为稳定内核排队补丁的各种工作流程的相关信息。
对于提交补丁的一般性信息，请参阅 `Documentation/process/submitting-patches.rst`。本文档仅描述与BPF相关的额外特定内容。

.. contents::
    :local:
    :depth: 2

报告错误
=========

问：如何报告BPF内核代码中的错误？
-----------------------------------
答：由于所有BPF内核开发以及bpftool和iproute2 BPF加载器的开发都是通过BPF内核邮件列表进行的，
请将发现的所有与BPF相关的问题报告到以下邮件列表：

 bpf@vger.kernel.org

这可能还包括与XDP、BPF跟踪等相关的问题。
鉴于netdev有很高的流量，请同时将BPF维护者添加到抄送（来自内核“MAINTAINERS”文件）：

* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

如果已经确定了导致问题的提交，请确保在报告中也把实际提交的作者添加到抄送。他们通常可以通过内核的git树来识别。
**请注意，不要向bugzilla.kernel.org报告BPF问题，因为这样报告的问题肯定会被忽略。**

提交补丁
========

问：在我发送补丁进行审核之前，如何在我的更改上运行BPF CI？
---------------------------------------------------------------------
答：BPF CI基于GitHub并托管在https://github.com/kernel-patches/bpf。虽然GitHub还提供了一个命令行界面(CLI)，可以用来完成相同的结果，但这里我们专注于基于用户界面(UI)的工作流程。
下面的步骤说明了如何开始你的补丁的CI运行：

- 在你自己的账户下创建上述仓库的一个分支（一次性操作）

- 本地克隆该分支，检出一个新的分支以跟踪bpf-next或bpf分支，并在此基础上应用你要测试的补丁

- 将本地分支推送到你的分支，并针对kernel-patches/bpf的bpf-next_base或bpf_base分支创建一个拉取请求

创建拉取请求后不久，CI工作流就会运行。请注意，其容量与提交上游的补丁检查共享，因此根据使用情况，运行可能需要一段时间才能完成。
此外，随着补丁被推送到它们所跟踪的相应上游分支，两个基础分支（bpf-next_base和bpf_base）都会被更新。因此，你的补丁集也会自动（尝试）重新基于新基线进行调整。
这种行为可能会导致CI运行被中止并重新启动新的基线。

问：我需要将我的BPF补丁提交到哪个邮件列表？
-------------------------------------------------
答：请将你的BPF补丁提交到BPF内核邮件列表：

 bpf@vger.kernel.org

如果你的补丁涉及多个不同的子系统（例如
翻译如下：

在网络编程、追踪、安全等领域中，确保抄送给相关的内核邮件列表和维护者，以便他们能够审查更改并为补丁提供他们的认可（Acked-by）。

问：在哪里可以找到当前正在讨论的BPF子系统的补丁？
-------------------------------------------------------------------------
答：所有抄送给netdev的补丁都会在netdev的Patchwork项目中排队等待审核：

  https://patchwork.kernel.org/project/netdevbpf/list/

那些针对BPF的补丁会被分配给一个“bpf”代表以供BPF维护者进一步处理。当前正在审核中的补丁队列可以在以下位置找到：

  https://patchwork.kernel.org/project/netdevbpf/list/?delegate=121173

一旦补丁被整个BPF社区审查并通过了BPF维护者的批准，它们在Patchwork中的状态将更改为“已接受”，并且提交者会通过电子邮件收到通知。这意味着从BPF的角度来看，这些补丁看起来很好，并且已经被应用到两个BPF内核树之一。
如果社区反馈需要对补丁进行重新编译，则其在Patchwork中的状态将设置为“请求更改”，并从当前的审核队列中移除。同样地，对于那些被拒绝或不适用于BPF树（但分配给了“bpf”代表）的补丁也是如此。

问：这些更改如何进入Linux？
------------------------------------------------
答：有两个BPF内核树（Git仓库）。一旦补丁被BPF维护者接受，它们将被应用到两个BPF树之一：

 * https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf.git/
 * https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/

bpf树本身仅用于修复，而bpf-next树则用于特性、清理或其他改进（类似“next”类的内容）。这类似于网络编程中的net和net-next树。bpf和bpf-next都只有一个主分支，以简化补丁应该基于哪个分支进行重置的问题。
bpf树中的累积BPF补丁将定期被拉入net内核树。同样地，被接受进入bpf-next树的累积BPF补丁将进入net-next树。net和net-next均由David S. Miller管理。从那里，它们将进入由Linus Torvalds管理的内核主线树。要了解net和net-next合并到主线树的过程，请参阅netdev子系统文档中的说明：
Documentation/process/maintainer-netdev.rst
偶尔地，为了避免合并冲突，我们可能会向其他树（例如追踪）发送包含少量补丁的小型拉取请求，但net和net-next始终是主要的目标集成树。
拉取请求将包含累积补丁的高级摘要，并可以通过以下主题行在netdev内核邮件列表中搜索（``yyyy-mm-dd``是拉取请求的日期）：

  pull-request: bpf yyyy-mm-dd
  pull-request: bpf-next yyyy-mm-dd

问：我如何指示我的补丁应该应用到哪个树（bpf与bpf-next）？
---------------------------------------------------------------------------------
  
答：这个过程与netdev子系统文档中描述的完全相同，即Documentation/process/maintainer-netdev.rst，请仔细阅读。主题行必须表明该补丁是一个修复还是“next”类内容，以便让维护者知道它是否针对bpf或bpf-next。
对于最终应进入bpf -> net树的修复，主题必须看起来像这样：

  git format-patch --subject-prefix='PATCH bpf' start..finish

对于应最终进入bpf-next -> net-next树的特性/改进等，主题必须看起来像这样：

  git format-patch --subject-prefix='PATCH bpf-next' start..finish

如果不确定补丁或补丁系列应该直接进入bpf或net，还是直接进入bpf-next或net-next，如果主题行指定了net或net-next作为目标，也没有问题。
最终决定权在于维护者来完成补丁的委派工作。
如果明确补丁应该进入bpf或bpf-next树，请确保将补丁基于这些树进行重置，以减少潜在的冲突。
如果补丁或补丁系列需要重新修改并再次以第二版或之后的版本发出，还需要在主题前缀中添加版本号（如`v2`、`v3`等）：

```shell
git format-patch --subject-prefix='PATCH bpf-next v2' start..finish
```

当补丁系列被要求进行更改时，应将整个补丁系列连同反馈一起重新发送（不要单独发送基于旧系列的差异文件）。

**问：补丁被应用到bpf或bpf-next树意味着什么？**
答：这意味着从BPF的角度看，该补丁看起来适合合并到主线。
请注意，这并不意味着该补丁将自动最终被接受进入net或net-next树：

在bpf内核邮件列表上，审查可能随时出现。如果围绕某个补丁的讨论得出结论认为它不能按原样被包含，我们可能会应用后续修复或完全从树中移除它们。因此，我们也保留根据需要对树进行重基的权利。毕竟，树的目的在于：
- i) 汇总和准备BPF补丁以供整合到net和net-next等树中；
- ii) 在补丁进一步发展之前运行广泛的BPF测试套件和工作负载。

一旦BPF拉取请求被David S. Miller接受，则这些补丁将分别进入net或net-next树，并从那里进一步进入主线。再次参考netdev子系统的文档（Documentation/process/maintainer-netdev.rst）获取更多信息，例如它们多久合并到主线一次。

**问：我需要等待多长时间才能得到关于我的BPF补丁的反馈？**
答：我们努力保持较低的反馈延迟。通常的反馈时间大约为2到3个工作日。这可能会根据变更的复杂性和当前的补丁负荷而变化。

**问：您多久向像net或net-next这样的主要内核树发送一次拉取请求？**
答：我们会经常发送拉取请求，以免在bpf或bpf-next中积累太多补丁。
作为一般规则，预计每个树会在周末定期发送拉取请求。在某些情况下，根据当前的补丁负荷或紧急程度，拉取请求也可能在周中发送。

**问：在合并窗口打开期间，bpf-next是否会处理补丁？**
答：在合并窗口打开的时间段内，不会处理bpf-next。这大致与net-next补丁处理方式相似，所以可以自由阅读netdev文档（Documentation/process/maintainer-netdev.rst）以了解详细信息。
在这两周的合并窗口期间，我们可能会要求您在bpf-next重新开放后重新发送您的补丁系列。一旦Linus发布了`v*-rc1`版本（合并窗口关闭后），我们将继续处理bpf-next。
对于没有订阅内核邮件列表的人，David S. Miller还运行了一个状态页面，提供关于net-next的指导：

  http://vger.kernel.org/~davem/net-next.html

**问：BPF验证器变更及测试用例**
**问：我对BPF验证器进行了更改，是否需要为BPF内核自测添加测试用例？**

答：如果补丁改变了验证器的行为，则是的，绝对有必要为BPF内核自测套件添加测试用例。如果没有这些测试用例而我们认为它们是必要的，那么在接受任何更改之前，我们可能会要求添加它们。
Specifically, `test_verifier.c` tracks a large number of BPF test cases, including many edge cases that the LLVM BPF backend may generate from the restricted C code. Therefore, adding test cases is absolutely critical to ensure that future changes do not unintentionally affect previous use cases. As such, consider these test cases as follows: verifier behavior that is not tracked in `test_verifier.c` could potentially be subject to change.

**Q:** Preference between `samples/bpf` and selftests?
------------------------------------------------------
**Q:** When should I add code to `samples/bpf/` and when to BPF kernel selftests_?

**A:** Generally, we prefer additions to BPF kernel selftests_ over `samples/bpf/`. The reason is quite straightforward: kernel selftests are regularly run by various bots to detect kernel regressions. The more test cases we add to BPF selftests, the better the coverage and the less likely they are to break accidentally. It’s not that BPF kernel selftests can’t demonstrate how a specific feature can be used.

However, `samples/bpf/` may be a good starting point for people, so it might be advisable to put simple demonstrations of features into `samples/bpf/`, but advanced functional and edge-case testing should go into kernel selftests. If your sample looks like a test case, opt for BPF kernel selftests instead!

**Q:** When should I add code to bpftool?
-----------------------------------------
**A:** The primary purpose of bpftool (located in tools/bpf/bpftool/) is to provide a centralized userspace tool for debugging and introspecting BPF programs and maps that are active in the kernel. If UAPI changes related to BPF enable the dumping of additional information about programs or maps, then bpftool should be extended accordingly to support this.

**Q:** When should I add code to iproute2's BPF loader?
--------------------------------------------------------
**A:** For UAPI changes related to the XDP or tc layer (e.g., `cls_bpf`), the convention is to add these control-path-related changes to iproute2's BPF loader from the userspace side as well. This is not only useful to ensure that UAPI changes are properly designed to be usable but also to make these changes available to a broader user base of major downstream distributions.

**Q:** Do you accept patches for iproute2's BPF loader?
--------------------------------------------------------
**A:** Patches for iproute2's BPF loader should be sent to:

  netdev@vger.kernel.org

Although these patches are not processed by the BPF kernel maintainers, please include them in CC so they can be reviewed.
The official git repository for iproute2 is maintained by Stephen Hemminger and can be found at:

  https://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git/

Patches need to have a subject prefix of `[PATCH iproute2 master]` or `[PATCH iproute2 net-next]`. ‘master’ or ‘net-next’ indicates the target branch where the patch should be applied. That is, if kernel changes were made to the net-next kernel tree, the related iproute2 changes should go into the iproute2 net-next branch; otherwise, they can be targeted at the master branch. The iproute2 net-next branch will be merged into the master branch after the current iproute2 version from master has been released.

Like BPF, the patches end up in patchwork under the netdev project and are delegated to ‘shemminger’ for further processing:

  http://patchwork.ozlabs.org/project/netdev/list/?delegate=389

**Q:** What is the minimum requirement before I submit my BPF patches?
---------------------------------------------------------------------
**A:** When submitting patches, always take the time to thoroughly test them *before* submission. Don’t rush them! If maintainers find that your patches haven’t been properly tested, it’s a good way to annoy them. Thorough testing of patch submissions is a strict requirement!

Note: Fixes that go into the bpf tree *must* include a `Fixes:` tag.
This also applies to fixes targeting bpf-next, where the affected commit is in net-next (or in some cases bpf-next). The `Fixes:` tag is crucial for identifying follow-up commits and significantly aids those who have to do backporting, so it is a must-have!

We also do not accept patches with empty commit messages. Take your time and write a high-quality commit message; it is essential!

Think of it this way: other developers looking at your code a month from now need to understand *why* a certain change was made in that way and whether there were flaws in the analysis or assumptions made by the original author. Therefore, providing a proper rationale and describing the use case for the changes is a must.
### 带有超过一个补丁的提交必须附带一封包含系列高级描述的封面信。这份高级概述将由BPF维护者放入合并提交中，以便将来可以从git日志中访问。

### Q: 改变BPF JIT和/或LLVM的功能
----------------------------------------

### Q: 添加新的指令或功能时，如果需要集成到BPF JIT和/或LLVM中，我需要注意什么？

A: 我们努力保持所有BPF JIT更新，以确保在不同架构上运行BPF程序时能获得相同的用户体验，即使内核中的BPF JIT启用的情况下也不使程序退回到效率较低的解释器。
如果你无法为某些架构实现或测试所需的JIT更改，请与相关的BPF JIT开发者合作，以便及时实施该功能。
请参考git日志(``arch/*/net/``)来找到必要的帮助人员。
同时始终确保为新指令添加BPF测试用例（例如 test_bpf.c 和 test_verifier.c），以便它们能够接受广泛的测试覆盖，并帮助运行时测试各种BPF JIT。
对于新的BPF指令，在更改被接受进入Linux内核后，请在LLVM的BPF后端实现支持。更多信息请参见下面的LLVM部分。
### 稳定版提交
==================

### Q: 我需要某个特定的BPF提交在稳定版内核中。我应该怎么做？
--------------------------------------------------------------------

A: 如果你需要某个特定的修复在稳定版内核中，首先检查该提交是否已经应用到了相关``linux-*.y``分支：

  https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git/

如果没有，则向BPF维护者发送邮件，并抄送给netdev内核邮件列表，请求将该修复加入队列：

  netdev@vger.kernel.org

通常的过程与netdev相同，详情请参阅网络子系统的文档：
Documentation/process/maintainer-netdev.rst

### Q: 您也会将提交回溯到当前未作为稳定版本维护的内核吗？
----------------------------------------------------------------------

A: 不会。如果你需要某个特定的BPF提交在当前未被稳定维护者维护的内核中，那么你需要自行处理。
当前稳定的和长期稳定的内核都列在这里：

  https://www.kernel.org/

### Q: 我即将提交的BPF补丁也需要在稳定版中应用
-------------------------------------------------------------------

我应该怎么做？

A: 与netdev补丁提交一般规则相同，详情请参阅netdev文档：
Documentation/process/maintainer-netdev.rst
不要在补丁说明中添加“``Cc: stable@vger.kernel.org``”，而是要求BPF维护者将补丁加入队列。这可以通过在补丁的``---``部分下做一个备注来完成，这部分不会记录到git日志中。或者，也可以通过简单的邮件请求来完成。
### 稳定队列补丁

**Q:** 在哪里可以找到当前已排队、将提交到稳定版本的 BPF 补丁？

**A:** 一旦修复关键错误的补丁被应用到 bpf 树中，它们会被排队在以下位置等待提交至稳定版本：

  http://patchwork.ozlabs.org/bundle/bpf/stable/?state=*

这些补丁会在那里至少等到与之相关的提交进入主线内核树。
经过更广泛的测试后，排队的补丁将由 BPF 维护者提交给稳定版本维护者。

### 测试补丁

#### 如何运行 BPF 自测

**A:** 在使用新编译的内核启动之后，导航到 BPF 自测套件以测试 BPF 功能（当前工作目录指向克隆的 git 树的根目录）：

```
$ cd tools/testing/selftests/bpf/
$ make
```

要运行验证器测试：

```
$ sudo ./test_verifier
```

验证器测试会打印出所有正在进行的检查。在运行完所有测试后，汇总信息将显示测试的成功和失败情况：

```
Summary: 418 PASSED, 0 FAILED
```

为了运行所有的 BPF 自测，需要执行以下命令：

```
$ sudo make run_tests
```

更多细节请参阅[内核自测文档](/dev-tools/kselftest)。

为了使尽可能多的测试通过，测试内核的 .config 应该尽可能接近 tools/testing/selftests/bpf 中的配置文件片段。

最后，为了确保支持最新的 BPF 类型格式特性——详情参见 [Documentation/bpf/btf.rst] ——当使用 CONFIG_DEBUG_INFO_BTF=y 编译内核时，需要 pahole 1.16 版本。

pahole 包含在 dwarves 包中，或者可以从源码构建，源码位于：

https://github.com/acmel/dwarves

从版本 1.13 和提交 21507cd3e97b ("pahole: 将 libbpf 作为子模块加入 lib/bpf") 开始，pahole 开始使用 libbpf 的定义和 API。

它与 git 仓库配合得很好，因为 libbpf 子模块会使用 "git submodule update --init --recursive" 进行更新。

不幸的是，默认的 Github 发布源代码不包含 libbpf 子模块的源代码，这会导致构建问题。来自 https://git.kernel.org/pub/scm/devel/pahole/pahole.git/ 的 tarball 与 Github 相同。你可以从以下位置获取带有相应 libbpf 子模块代码的源码 tarball：

https://fedorapeople.org/~acme/dwarves

一些发行版已经打包了 pahole 1.16 版本，例如 Fedora 和 Gentoo。

#### 我应该使用哪个版本的 BPF 内核自测来测试我的内核？

**A:** 如果你运行的是内核 `xyz`，那么你应该总是使用相同版本 `xyz` 的 BPF 内核自测进行测试。不要期望最新的主线树中的 BPF 自测能一直通过所有的测试。
特别是在 test_bpf.c 和 test_verifier.c 中有大量的测试案例，并且这些测试案例会持续更新以包含新的 BPF 测试序列，或者根据验证器的变化（例如验证器变得更智能并能更好地跟踪某些内容）来调整现有的测试案例。

LLVM
====

问：我在哪里可以找到支持 BPF 的 LLVM？
-----------------------------------------
答：自版本 3.7.1 起，LLVM 的 BPF 后端已经集成到了上游 LLVM 中。
如今所有主要的发行版都提供带有 BPF 后端的 LLVM，因此对于大多数使用场景来说，不再需要手动编译 LLVM，只需安装发行版提供的软件包即可。
LLVM 的静态编译器通过 `llc --version` 命令列出支持的目标，确保 BPF 目标被列出。示例如下：

     $ llc --version
     LLVM (http://llvm.org/):
       LLVM version 10.0.0
       Optimized build
Default target: x86_64-unknown-linux-gnu
       Host CPU: skylake

       Registered Targets:
         aarch64    - AArch64 (little endian)
         bpf        - BPF (host endian)
         bpfeb      - BPF (big endian)
         bpfel      - BPF (little endian)
         x86        - 32-bit X86: Pentium-Pro and above
         x86-64     - 64-bit X86: EM64T and AMD64

为了利用 LLVM 的 BPF 后端中添加的最新功能，开发人员建议运行最新的 LLVM 版本。对新 BPF 内核功能的支持，如 BPF 指令集的扩展，通常是与 LLVM 的发展同步进行的。
所有的 LLVM 发布版本可以在以下位置找到：http://releases.llvm.org/

问：明白了，那么如果我无论如何都需要手动构建 LLVM 怎么做呢？
--------------------------------------------------
答：我们推荐希望获得最快增量构建的开发人员使用 Ninja 构建系统，你可以在系统的包管理器中找到它，通常包名为 ninja 或者 ninja-build。
你需要 ninja、cmake 和 gcc-c++ 作为 LLVM 的构建依赖项。一旦你准备好了这些，就可以开始从 git 仓库构建最新的 LLVM 和 clang 版本了：

     $ git clone https://github.com/llvm/llvm-project.git
     $ mkdir -p llvm-project/llvm/build
     $ cd llvm-project/llvm/build
     $ cmake .. -G "Ninja" -DLLVM_TARGETS_TO_BUILD="BPF;X86" \
                -DLLVM_ENABLE_PROJECTS="clang"    \
                -DCMAKE_BUILD_TYPE=Release        \
                -DLLVM_BUILD_RUNTIME=OFF
     $ ninja

构建后的二进制文件可以在 build/bin/ 目录下找到，你可以将 PATH 环境变量指向这个目录。
将 ``-DLLVM_TARGETS_TO_BUILD`` 设置为你希望构建的目标，你可以在 llvm-project/llvm/lib/Target 目录下找到完整的目标列表。

问：报告 LLVM BPF 问题
----------------------------
问：我是否应该向 BPF 内核维护者报告 LLVM 的 BPF 代码生成后端中的问题或 LLVM 生成的代码被验证器拒绝接受的问题？

答：是的，请这样做！

LLVM 的 BPF 后端是整个 BPF 基础设施的关键组成部分，并且它与内核侧的程序验证紧密相关。因此，任何一方出现的问题都需要调查和修复。
因此，请务必在 netdev 内核邮件列表中提出这些问题，并抄送给 LLVM 和内核部分的 BPF 维护者：

* Yonghong Song <yhs@fb.com>
* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

LLVM 也有一个用于跟踪 BPF 相关 bug 的问题追踪器：

  https://bugs.llvm.org/buglist.cgi?quicksearch=bpf

然而，通过邮件列表并抄送维护者的方式可能会更有效。
---

**Q: 新的 BPF 指令用于内核和 LLVM**

---

**Q:** 我已经在内核中添加了一个新的 BPF 指令，如何将其集成到 LLVM 中？

**A:** LLVM 为 BPF 后端提供了一个 `-mcpu` 选择器，以便能够选择 BPF 指令集扩展。默认情况下使用 `generic` 处理器目标，这是 BPF 的基础指令集（版本 1）。

LLVM 提供了一个选项来选择 `-mcpu=probe`，它会探测主机内核支持的 BPF 指令集扩展，并自动选择最优的一组。

对于交叉编译，也可以手动选择特定版本：

```shell
$ llc -march bpf -mcpu=help
可用的 CPU 目标有：

  generic - 选择通用处理器
  probe   - 选择探测处理器
  v1      - 选择版本 1 处理器
  v2      - 选择版本 2 处理器
  [...]
```

在 Linux 内核中新增加的 BPF 指令需要遵循相同的方案：提升指令集版本，并实现扩展探测功能，使得使用 `-mcpu=probe` 的用户在升级他们的内核时可以透明地从中受益。

如果你无法实现对新增 BPF 指令的支持，请联系 BPF 开发者寻求帮助。

顺便说一下，BPF 内核自测是使用 `-mcpu=probe` 运行的，以获得更好的测试覆盖率。

---

**Q: 目标为 BPF 的 clang 标志？**

---

**Q:** 在某些情况下使用 clang 标志 `--target=bpf`，但在其他情况下则使用与底层架构匹配的默认 clang 目标。
LLVM IR生成和优化试图保持架构无关性，但`--target=<arch>`仍然对生成的代码有一定影响：

- BPF程序可能递归包含带有文件作用域内联汇编代码的头文件。默认目标可以很好地处理这种情况，而`bpf`目标在BPF后端汇编器不理解这些汇编代码时可能会失败，这在大多数情况下是真实的。
- 当没有使用`-g`编译时，默认目标可能会在目标文件中生成额外的ELF段（例如`.eh_frame`和`.rela.eh_frame`），而在`bpf`目标下则不会生成这些段。
- 默认目标可能会将C语言中的`switch`语句转换为通过查找表进行跳转的操作。由于这个查找表被放置在全局只读区域，因此BPF程序加载时会失败。`bpf`目标不支持这种查找表优化。可以通过Clang选项`-fno-jump-tables`禁用查找表生成。
- 对于Clang的`--target=bpf`，无论底层Clang二进制文件或默认目标（或内核）是否为32位，都可以保证指针或`long`/`unsigned long`类型始终具有64位宽度。然而，当使用原生Clang目标时，它将根据底层架构的约定来编译这些类型，这意味着对于32位架构，BPF上下文结构中的指针或`long`/`unsigned long`类型的宽度将为32位，而BPF LLVM后端仍以64位操作。原生目标主要用于追踪场景，如遍历`pt_regs`或其他内核结构，其中CPU寄存器宽度很重要。
- 否则，一般建议使用`clang --target=bpf`。

您应该在以下情况下使用默认目标：

- 您的程序包含了头文件（例如`ptrace.h`），该头文件最终引入了一些包含文件作用域主机汇编代码的头文件。
- 您可以添加`-fno-jump-tables`来解决查找表问题。
- 否则，您可以使用`bpf`目标。此外，您**必须**使用`bpf`目标的情况包括：
  
- 您的程序使用了包含指针或`long`/`unsigned long`类型的数据结构，并且这些数据结构与BPF辅助函数或上下文数据结构交互。访问这些结构会被BPF验证器验证，并可能导致验证失败，如果原生架构与BPF架构（例如64位）不一致。一个例子是BPF_PROG_TYPE_SK_MSG需要`--target=bpf`。

.. 链接
.. _selftests:
   https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/

祝您编写BPF愉快！
