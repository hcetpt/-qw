稳定 API 无意义标签：

Linux 内核驱动接口
==================

（解答您所有的问题，甚至更多）

Greg Kroah-Hartman <greg@kroah.com>

本文旨在解释为什么 Linux **没有二进制内核接口，也没有稳定的内核接口**。
.. note::

  请注意，本文描述的是**内核内部**的接口，而不是内核到用户空间的接口。
  内核到用户空间的接口是应用程序使用的，即系统调用接口。这个接口**非常**稳定，
  随着时间推移不会破坏。我有一些在 0.9 某版本之前的内核上构建的老程序，它们在最新的 2.6 版本内核上仍然运行良好。
  这个接口是用户和应用程序开发人员可以依赖的稳定接口。

执行摘要
---------
你可能认为自己想要一个稳定的内核接口，但实际上你并不需要，甚至你都不知道这一点。你真正想要的是一个稳定运行的驱动程序，而只有当你的驱动程序位于主内核树中时，你才能得到这样的驱动程序。如果驱动程序位于主内核树中，你会得到许多其他好处，这些好处共同使 Linux 成为一个强大、稳定且成熟的操作系统，这也是你选择使用它的原因。

引言
----
只有少数想编写内核驱动的人需要担心内核内部接口的变化。对于大多数世界而言，他们既看不见这个接口，也不关心它。

首先，我不会讨论任何与闭源、隐藏源代码、二进制块、源代码包装器等术语相关的法律问题，这些术语用来描述未根据 GPL 发布源代码的内核驱动程序。如果你有任何法律问题，请咨询律师。我是一个程序员，因此在这里我将仅描述技术问题（并非轻视法律问题，它们确实存在，并且你需要始终关注它们）。

这里主要有两个主题：二进制内核接口和稳定的内核源码接口。这两个主题相互依赖，但我们将先讨论二进制接口以尽快解决这个问题。

二进制内核接口
---------------
假设我们有了一个稳定的内核源码接口，那么自然也会有一个二进制接口，对吧？不正确。请考虑以下关于 Linux 内核的事实：

  - 根据你使用的 C 编译器版本，不同的内核数据结构可能会包含不同结构的对齐方式，以及可能以不同方式包含不同的函数（内联或非内联）。函数的具体组织不是很重要，但不同数据结构的填充非常重要。
  - 根据你选择的内核构建选项，内核可以做出广泛的假设：

      - 不同的结构可能包含不同的字段
      - 某些功能可能根本就没有实现，（例如，在非 SMP 构建中某些锁可能被编译为不存在）
      - 内核中的内存可以根据构建选项以不同的方式进行对齐
  - Linux 在广泛的不同处理器架构上运行
一种架构下的二进制驱动程序不可能在另一种架构下正常运行。
通过仅仅为确切特定的内核配置编译你的模块，并使用与构建内核时完全相同的 C 编译器，可以解决许多这些问题。如果你想要为某一特定 Linux 发行版的特定发布版本提供一个模块，这样做就足够了。但将这一单独的构建乘以不同 Linux 发行版的数量以及这些发行版支持的不同版本数量，你很快就会面临不同版本中的各种构建选项所带来的噩梦。同时要意识到每个 Linux 发行版发布都包含了多个不同的内核，它们都被调整以适应不同类型的硬件（不同的处理器类型和不同的选项），因此即使对于单一的发布版本，你也需要创建多个模块版本。
相信我，随着时间的推移，如果你试图支持这种类型的发布，你会变得疯狂，这是我在很久以前通过痛苦的方式学到的教训。
稳定的内核源接口
-------------------

如果你和那些尝试长时间维护不在主内核树中的 Linux 内核驱动程序的人交谈，这将是一个更加“不稳定”的话题。
Linux 内核的发展是持续且快速的，从不停止减速。因此，内核开发者会发现现有接口中的错误，或者找到更好的实现方法。如果他们找到了改进的方法，他们会修复现有的接口使其工作得更好。当这种情况发生时，函数名称可能会改变，结构可能会扩大或缩小，函数参数可能被重构。如果出现这种情况，所有使用这个接口的地方都会在同一时间进行修正，以确保一切继续正常工作。
作为一个具体的例子，在这个子系统的生命周期中，内核内的 USB 接口至少经历了三次重大的重构。这些重构是为了解决一些不同的问题：

- 从同步的数据流模型转变为异步模型。这降低了大量驱动程序的复杂性，并提高了所有 USB 驱动程序的吞吐量，使我们能够几乎以最大速度运行所有的 USB 设备。
- 在 USB 核心分配数据包的方式上进行了改变，使得所有驱动程序现在需要向 USB 核心提供更多信息来解决已记录的死锁问题。

这与一些必须长期维护旧版 USB 接口的闭源操作系统形成了鲜明对比。这导致新开发者可能无意中使用旧接口，从而以不正确的方式做事，进而影响操作系统的稳定性。
在这两种情况下，所有开发者都认为这些改变是重要的并且必须做出，而且它们也被实现了，相对没有太多痛苦。如果 Linux 必须保证保持稳定的源接口，那么就会创建一个新的接口，而旧的、有问题的接口将不得不长期维护，这会给 USB 开发者带来额外的工作。由于所有 Linux USB 开发者都是在自己的空闲时间完成工作的，要求程序员无偿地做额外工作而不获得任何收益是不可能的。
安全问题对 Linux 来说也是非常重要的。当发现安全问题时，它会在很短的时间内得到修复。很多时候，这会导致内核内部接口被重构以防止安全问题的发生。当这种情况发生时，所有使用这些接口的驱动程序也会在同一时间被修正，确保安全问题被修复，并且不会在未来某个时候意外重现。如果内部接口不允许改变，修复这类安全问题并确保其不再发生的可能性就不存在了。
### 内核接口随时间清理
随着时间的推移，内核接口会被逐步清理。如果某个当前接口无人使用，则会被删除。这样做可以确保内核尽可能地精简，并且所有潜在的接口都能得到尽可能充分的测试（未使用的接口几乎不可能进行有效性测试）。

### 应该如何做
#### 如果你有一个不在主内核树中的Linux内核驱动程序，作为开发者你应该怎么办？
为每个不同的内核版本和每个发行版发布二进制驱动程序是一个噩梦，同时跟上不断变化的内核接口也是一个艰巨的任务。
解决方法很简单：让你的内核驱动程序进入主内核树（这里我们讨论的是在GPL兼容许可下发布的驱动程序，如果你的代码不属于此类别，祝你好运，你将自行解决这个问题）。如果你的驱动程序在主树中，当内核接口发生变化时，最初做出内核更改的人会负责修复。这保证了你的驱动程序总是可构建的，并且随着时间的推移始终能正常工作，而无需你付出太多努力。
将你的驱动程序放入主内核树中的非常积极的影响包括：

- 驱动程序的质量将提高，因为维护成本（对于原始开发者来说）将会降低。
- 其他开发者会为你的驱动程序添加功能。
- 其他人会发现并修复你的驱动程序中的错误。
- 其他人会在你的驱动程序中找到优化的机会。
- 当外部接口变更需要更新时，其他人会为你更新驱动程序。
- 驱动程序自动包含在所有Linux发行版中，无需请求发行版添加它。

由于Linux支持的设备种类比任何其他操作系统都要多，并且这些设备的支持跨越了更多的处理器架构，这种经过验证的开发模式显然有其正确之处。

### 致谢
感谢Randy Dunlap、Andrew Morton、David Brownell、Hanna Linder、Robert Love以及Nishanth Aravamudan对本文早期草稿的审阅和建议。
