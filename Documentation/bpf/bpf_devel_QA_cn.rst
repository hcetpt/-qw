如何与BPF子系统交互
====================

本文档提供了关于报告错误、提交补丁以及为稳定内核排队补丁等各种工作流程的BPF子系统相关信息。对于提交补丁的一般信息，请参阅 `Documentation/process/submitting-patches.rst`。本文档仅描述与BPF相关的额外具体事项。
.. contents::
    :local:
    :depth: 2

报告错误
=========

问：我如何报告BPF内核代码中的错误？
-------------------------------------
答：由于所有的BPF内核开发以及bpftool和iproute2 BPF加载器开发都是通过bpf内核邮件列表进行的，请将发现的所有有关BPF的问题报告到以下邮件列表：

 bpf@vger.kernel.org

这可能还包括与XDP、BPF追踪等有关的问题。
鉴于netdev有大量的邮件流量，报告问题时请同时将BPF维护者添加到抄送(Cc)中（从内核 `MAINTAINERS` 文件获取）：

* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

如果已经确定了引起错误的提交，请确保在报告时也把该提交的作者添加到抄送中。这些作者通常可以通过内核的git树来识别。
**请注意不要向bugzilla.kernel.org报告BPF问题，因为这样报告的问题很可能会被忽视。**

提交补丁
========

问：我在发送补丁以供审核之前如何运行BPF持续集成(CI)？
-------------------------------------------------------
答：BPF CI基于GitHub并托管在 https://github.com/kernel-patches/bpf 。虽然GitHub也提供了一个命令行界面(CLI)，可以用来实现相同的结果，但这里我们专注于基于用户界面(UI)的工作流程。
以下步骤说明了如何为您的补丁启动CI运行：

- 在您自己的帐户中创建上述仓库的一个分支（只需执行一次）

- 本地克隆这个分支，检查出一个新的分支来跟踪bpf-next或bpf分支，并在此基础上应用您要测试的补丁。

- 将本地分支推送到您的分支，并针对kernel-patches/bpf的bpf-next_base或bpf_base分支创建一个拉取请求。

在创建拉取请求后不久，CI工作流就会运行。请注意，CI的容量是与上游提交的补丁一起共享的，因此根据使用情况，运行可能需要一段时间才能完成。
此外，请注意两个基础分支（bpf-next_base和bpf_base）都会随着它们跟踪的上游分支更新而更新。因此，您的补丁集也会自动（尝试）重新基于新的基线。
这种行为可能导致CI运行被中止并以新的基线重启。
问：我需要将我的BPF补丁提交到哪个邮件列表？
-------------------------------------------------
答：请将您的BPF补丁提交到bpf内核邮件列表：

 bpf@vger.kernel.org

如果您补丁涉及多个不同的子系统（例如
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
答：该过程与netdev子系统文档中描述的完全相同，在Documentation/process/maintainer-netdev.rst中有详细说明，请仔细阅读。主题行必须表明补丁是修复还是“next”类内容，以便让维护者知道它是否针对bpf或bpf-next。
对于最终将进入bpf -> net树的修复，主题必须看起来像这样：

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

**问：当一个补丁被应用到bpf或bpf-next树中意味着什么？**
答：这意味着从BPF的角度来看，该补丁看起来适合主分支的合并。
请注意，这并不意味着该补丁将自动最终被net或net-next树接受：

在bpf内核邮件列表中，审查可能随时发生。如果围绕某个补丁的讨论得出结论认为它不能直接被包含进去，我们可能会应用后续修复或完全放弃这些补丁。因此，在必要时我们也保留对树进行重基的权利。毕竟，树的目的在于：
- i) 汇总和准备BPF补丁以供net和net-next等树合并，
- ii) 在补丁进一步发展之前运行广泛的BPF测试套件及工作负载。

一旦BPF拉取请求被David S. Miller接受，那么补丁就会进入net或net-next树，并从那里进一步进入主分支。详情请参阅netdev子系统的文档`Documentation/process/maintainer-netdev.rst`，例如它们多久合并一次至主分支。

**问：我需要等待多久才能得到我的BPF补丁的反馈？**
答：我们会尽量保持反馈时间短。通常情况下，反馈时间大约为2到3个工作日。根据变更的复杂性和当前的补丁负荷，这个时间可能会有所不同。

**问：您多久向像net或net-next这样的主要内核树发送拉取请求？**
答：为了不使bpf或bpf-next树积累过多的补丁，我们会经常发送拉取请求。
一般而言，请预期每个树在周末末尾定期会有拉取请求。在某些情况下，根据当前的补丁负荷或紧急程度，拉取请求也可能在周中发出。

**问：当合并窗口打开时，bpf-next中的补丁会被处理吗？**
答：当合并窗口打开时，不会处理bpf-next中的补丁。这与处理net-next补丁大致相同，因此您可以自由阅读netdev文档`Documentation/process/maintainer-netdev.rst`了解更多细节。
在这两周的合并窗口期间，我们可能会要求您在bpf-next重新开放后重新发送您的补丁系列。一旦Linus发布了`v*-rc1`版本（合并窗口关闭后），我们将继续处理bpf-next。
对于没有订阅内核邮件列表的人，David S. Miller还运行了一个状态页面，提供关于net-next的指导：

  http://vger.kernel.org/~davem/net-next.html

**问：BPF验证器变更和测试用例**
**问：我对BPF验证器进行了更改，是否需要为BPF内核自测添加测试用例？**

答：如果补丁改变了验证器的行为，则是的，绝对有必要为BPF内核自测套件添加测试用例。如果没有这些测试用例而我们认为它们是必要的，那么在接受任何更改之前，我们可能会要求添加这些测试用例。
Specifically, `test_verifier.c` tracks a large number of BPF test cases, including many edge cases that the LLVM BPF backend may generate from the restricted C code. Therefore, adding test cases is absolutely critical to ensure that future changes do not unintentionally affect previous use cases. As such, consider these test cases as follows: verifier behavior that is not tracked in `test_verifier.c` could potentially be subject to change.

**Q: Preference for `samples/bpf` versus selftests?**

**Q: When should I add code to `samples/bpf/` and when to BPF kernel selftests_?**

**A:** Generally, we prefer additions to BPF kernel selftests_ over `samples/bpf/`. The reasoning is quite straightforward: kernel selftests are regularly run by various bots to detect kernel regressions. The more test cases we add to BPF selftests, the better the coverage and the less likely they are to break accidentally. It's not that BPF kernel selftests can't demonstrate how a specific feature can be used.

However, `samples/bpf/` may be a good starting point for beginners, so it might be advisable to put simple demonstrations of features into `samples/bpf/`, while advanced functional and edge-case testing should go into kernel selftests. If your sample looks like a test case, opt for BPF kernel selftests instead!

**Q: When should I add code to bpftool?**

**A:** The primary purpose of bpftool (located in tools/bpf/bpftool/) is to provide a centralized userspace tool for debugging and introspecting BPF programs and maps that are active in the kernel. If UAPI changes related to BPF enable the dumping of additional information about programs or maps, then bpftool should also be extended to support their dumping.

**Q: When should I add code to iproute2's BPF loader?**

**A:** For UAPI changes related to the XDP or tc layer (e.g., `cls_bpf`), the convention is to add control-path-related changes to iproute2's BPF loader from the userspace side as well. This is not only useful for ensuring that UAPI changes are properly designed to be usable, but also for making these changes available to a broader user base of major downstream distributions.

**Q: Do you accept patches for iproute2's BPF loader as well?**

**A:** Patches for iproute2's BPF loader should be sent to:

  netdev@vger.kernel.org

Although these patches are not processed by the BPF kernel maintainers, please include them in the CC list so they can be reviewed. The official git repository for iproute2 is maintained by Stephen Hemminger and can be found at:

  https://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git/

Patches need to have a subject prefix of `[PATCH iproute2 master]` or `[PATCH iproute2 net-next]`. `master` or `net-next` indicates the target branch where the patch should be applied. That is, if kernel changes were merged into the net-next kernel tree, then the related iproute2 changes need to go into the iproute2 net-next branch; otherwise, they can be targeted at the master branch. The iproute2 net-next branch will be merged into the master branch after the current iproute2 version from master has been released.

Similar to BPF, patches end up in patchwork under the netdev project and are delegated to `shemminger` for further processing:

  http://patchwork.ozlabs.org/project/netdev/list/?delegate=389

**Q: What is the minimum requirement before I submit my BPF patches?**

**A:** When submitting patches, always take the time to properly test your patches *before* submission. Never rush them! If maintainers find that your patches have not been adequately tested, it's a surefire way to annoy them. Testing patch submissions is a strict requirement!

Note that fixes going to the bpf tree *must* include a `Fixes:` tag. The same applies to fixes targeting bpf-next, where the affected commit is in net-next (or in some cases bpf-next). The `Fixes:` tag is crucial for identifying follow-up commits and significantly aids those who have to do backporting, so it is a must-have!

We also do not accept patches with empty commit messages. Take your time and write a high-quality commit message; it's essential!

Think of it this way: other developers looking at your code a month from now need to understand *why* a certain change was made in that way, and whether there were any flaws in the analysis or assumptions made by the original author. Therefore, providing a proper rationale and describing the use case for the changes is a must.
### 带有超过一个补丁的提交必须附带一封包含系列高级描述的封面信。这份高级概述将由BPF维护者放入合并提交中，以便将来可以从git日志中访问。

### Q: 改变BPF JIT和/或LLVM的功能
----------------------------------------

### Q: 添加新的指令或功能时，如果需要集成到BPF JIT和/或LLVM中，我需要注意什么？

A: 我们努力保持所有BPF JIT更新，以确保在不同架构上运行BPF程序时能获得相同的用户体验，即使内核中的BPF JIT启用的情况下也不使程序退回到效率较低的解释器。
如果你无法为某些架构实现或测试所需的JIT更改，请与相关的BPF JIT开发者合作，以便及时实施该功能。
请参考git日志(``arch/*/net/``)来找到必要的帮助人员。
同时始终确保为新指令添加BPF测试用例（例如 test_bpf.c 和 test_verifier.c），以便它们能够接受广泛的测试覆盖，并帮助运行时测试各种BPF JIT。
对于新的BPF指令，在更改被接受进入Linux内核后，请在LLVM的BPF后端中实现支持。更多信息请参见下面的LLVM部分。
### 稳定版提交
=================

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

从版本 1.13 和提交 21507cd3e97b ("pahole: 将 libbpf 作为子模块添加到 lib/bpf") 开始，pahole 开始使用 libbpf 的定义和 API。

由于它很好地与 git 仓库配合工作，`git submodule update --init --recursive` 命令将用于更新 libbpf 子模块。

不幸的是，默认的 Github 发布源代码不包含 libbpf 子模块源代码，这会导致构建问题。从 https://git.kernel.org/pub/scm/devel/pahole/pahole.git/ 获取的 tarball 文件与 Github 相同，你可以从以下链接获取包含相应 libbpf 子模块代码的源码 tarball：

https://fedorapeople.org/~acme/dwarves

一些发行版已经打包了 pahole 1.16 版本，例如 Fedora 和 Gentoo。

#### 我应该用哪个版本的 BPF 内核自测来测试我的内核？

**A:** 如果你正在使用内核“xyz”，那么你应该始终使用该内核“xyz”的 BPF 内核自测。不要期望最新的主线树中的 BPF 自测总是能通过所有的测试。
特别是在 test_bpf.c 和 test_verifier.c 中有大量的测试案例，并且这些测试案例会持续更新以包含新的 BPF 测试序列，或者根据验证器的变化（例如验证器变得更智能并能更好地跟踪某些方面）来调整现有的测试案例。

LLVM
====

问：我在哪里可以找到支持 BPF 的 LLVM？
-----------------------------------------
答：自版本 3.7.1 起，LLVM 的 BPF 后端已经集成到了上游的 LLVM 中。
如今，所有主要发行版都附带了启用了 BPF 后端的 LLVM，因此对于大多数使用场景来说，不再需要手动编译 LLVM，只需安装发行版提供的包即可。
LLVM 的静态编译器通过 `llc --version` 命令列出支持的目标，请确保列出了 BPF 目标。示例如下：

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

对于开发者而言，为了利用 LLVM 的 BPF 后端中添加的最新特性，建议运行最新的 LLVM 版本。对新的 BPF 内核特性的支持（如 BPF 指令集的增加）通常是与 LLVM 的开发同步进行的。
所有 LLVM 发布版本都可以在以下网址找到：http://releases.llvm.org/

问：明白了，那么我如何手动构建 LLVM 呢？
--------------------------------------------------
答：我们建议希望获得最快增量构建的开发者使用 Ninja 构建系统，您可以在系统的包管理器中找到它，通常该包名为 ninja 或 ninja-build。
您需要 ninja、cmake 和 gcc-c++ 作为 LLVM 的构建前提条件。一旦您具备这些条件，就可以继续从 Git 仓库构建最新的 LLVM 和 Clang 版本：

     $ git clone https://github.com/llvm/llvm-project.git
     $ mkdir -p llvm-project/llvm/build
     $ cd llvm-project/llvm/build
     $ cmake .. -G "Ninja" -DLLVM_TARGETS_TO_BUILD="BPF;X86" \
                -DLLVM_ENABLE_PROJECTS="clang"    \
                -DCMAKE_BUILD_TYPE=Release        \
                -DLLVM_BUILD_RUNTIME=OFF
     $ ninja

构建后的二进制文件可以在 build/bin/ 目录下找到，您可以将 PATH 变量指向该目录。
设置 ``-DLLVM_TARGETS_TO_BUILD`` 为您希望构建的目标，您可以在 llvm-project/llvm/lib/Target 目录中找到目标的完整列表。

问：报告 LLVM 的 BPF 问题
----------------------------
问：当 LLVM 的 BPF 代码生成后端出现问题时，或当验证器拒绝接受由 LLVM 生成的代码时，我是否应该通知 BPF 内核维护者？

答：是的，请这样做！

LLVM 的 BPF 后端是整个 BPF 基础设施的关键部分，并且与内核侧的程序验证紧密相关。因此，任何一方的问题都需要调查并在必要时修复。
因此，请务必在 netdev 内核邮件列表上提出这些问题，并抄送给 LLVM 和内核部分的 BPF 维护者：

* Yonghong Song <yhs@fb.com>
* Alexei Starovoitov <ast@kernel.org>
* Daniel Borkmann <daniel@iogearbox.net>

LLVM 也有一个用于查找 BPF 相关错误的问题追踪器：

  https://bugs.llvm.org/buglist.cgi?quicksearch=bpf

然而，通过邮件列表并抄送维护者的方式联系会更好。
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

如果你无法实现对新添加的 BPF 指令的支持，请联系 BPF 开发者寻求帮助。

顺便说一下，BPF 内核自检测试是使用 `-mcpu=probe` 进行的，以获得更好的测试覆盖率。

---

**Q: 对于目标 bpf 的 clang 标志？**

---

**Q:** 在某些情况下使用了 clang 标志 `--target=bpf`，而在其他情况下则使用与底层架构匹配的默认 clang 目标。
LLVM IR生成和优化试图保持架构无关性，但`--target=<arch>`仍然对生成的代码有一定影响：

- BPF程序可能递归包含带有文件作用域内联汇编代码的头文件。默认目标可以很好地处理这种情况，而`bpf`目标在BPF后端汇编器不理解这些汇编代码时可能会失败，这在大多数情况下是真实的。
- 当没有使用`-g`编译时，默认目标可能会在目标文件中生成额外的ELF段（例如`.eh_frame`和`.rela.eh_frame`），而在`bpf`目标下则不会生成这些段。
- 默认目标可能会将C语言中的`switch`语句转换为通过查找表进行跳转的操作。由于这个查找表被放置在全局只读区域，因此BPF程序加载时会失败。`bpf`目标不支持这种查找表优化。可以通过Clang选项`-fno-jump-tables`来禁用查找表生成。
- 对于Clang `--target=bpf`，可以保证指针或`long`/`unsigned long`类型总是具有64位宽度，无论Clang二进制文件、默认目标（或内核）本身是否为32位。然而，当使用原生Clang目标时，它将根据底层架构约定来编译这些类型，这意味着对于32位架构，指针或`long`/`unsigned long`类型（例如，在BPF上下文结构中）将具有32位宽度，而BPF LLVM后端仍然以64位运行。原生目标主要用于追踪场景中，如遍历`pt_regs`或其他内核结构时，CPU寄存器宽度很重要。
除此之外，通常推荐使用`clang --target=bpf`。

您应该使用默认目标的情况如下：

- 您的程序包含了头文件（例如`ptrace.h`），该头文件最终引入了一些包含文件作用域主机汇编代码的头文件。
- 您可以添加`-fno-jump-tables`来解决查找表问题。
否则，您可以使用`bpf`目标。此外，您**必须**使用`bpf`目标的情况包括：

- 您的程序使用了包含指针或`long`/`unsigned long`类型的与BPF辅助函数或上下文数据结构交互的数据结构。访问这些结构将由BPF验证器进行验证，并可能导致验证失败，如果原生架构与BPF架构不一致（例如64位）。一个例子是BPF_PROG_TYPE_SK_MSG需要使用`--target=bpf`。

.. 链接
.. _selftests:
   https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/

祝您愉快地进行BPF开发！
