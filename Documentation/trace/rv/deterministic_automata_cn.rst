确定性自动机
======================

形式上，一个确定性自动机 G 定义为一个五元组：

        *G* = { *X*, *E*, *f*, x\ :subscript:`0`, X\ :subscript:`m` }

其中：

- *X* 是状态集合；
- *E* 是有限事件集合；
- x\ :subscript:`0` 是初始状态；
- X\ :subscript:`m`（*X* 的子集）是标记状态（或最终状态）集合；
- *f* : *X* x *E* -> *X* 是转换函数。它定义了当事件 *E* 在状态 *X* 发生时的状态转移。在确定性自动机的特殊情况下，事件 *E* 在状态 *X* 中的发生会导致一个确定性的下一个状态 *X*。

例如，一个名为 'wip'（抢占唤醒）的自动机可以定义为：

- *X* = { ``抢占式``, ``非抢占式``}
- *E* = { ``启用抢占``, ``禁用抢占``, ``调度唤醒``}
- x\ :subscript:`0` = ``抢占式``
- X\ :subscript:`m` = {``抢占式``}
- *f* =
   - *f*\ (``抢占式``, ``禁用抢占``) = ``非抢占式``
   - *f*\ (``非抢占式``, ``调度唤醒``) = ``非抢占式``
   - *f*\ (``非抢占式``, ``启用抢占``) = ``抢占式``

这种形式化定义的一个好处是可以以多种格式呈现。例如，使用图形表示法，使用顶点（节点）和边，这对于操作系统从业者来说非常直观，并且没有任何损失。
之前的 'wip' 自动机也可以表示为：

                       启用抢占
          +---------------------------------+
          v                                 |
        #============#  禁用抢占   +------------------+
    --> H 抢占式 H -----------------> |  非抢占式  |
        #============#                    +------------------+
                                            ^              |
                                            | 调度唤醒 |
                                            +--------------+

C语言中的确定性自动机
----------------------------

在论文“Linux内核的有效形式验证”中，作者提出了一个简单的方法来表示可以在Linux内核中作为常规代码使用的自动机。
例如，'wip' 自动机可以表示为（加上注释）：

  /* 枚举表示 X（状态集合），用于索引 */
  enum states {
	preemptive = 0,
	non_preemptive,
	state_max
  };

  #define INVALID_STATE state_max

  /* 枚举表示 E（事件集合），用于索引 */
  enum events {
	preempt_disable = 0,
	preempt_enable,
	sched_waking,
	event_max
  };

  struct automaton {
	char *state_names[state_max];                   // X: 状态集合
	char *event_names[event_max];                   // E: 有限事件集合
	unsigned char function[state_max][event_max];   // f: 转换函数
	unsigned char initial_state;                    // x_0: 初始状态
	bool final_states[state_max];                   // X_m: 标记状态集合
  };

  struct automaton aut = {
	.state_names = {
		"抢占式",
		"非抢占式"
	},
	.event_names = {
		"禁用抢占",
		"启用抢占",
		"调度唤醒"
	},
	.function = {
		{ non_preemptive,  INVALID_STATE,  INVALID_STATE },
		{  INVALID_STATE,     preemptive, non_preemptive },
	},
	.initial_state = preemptive,
	.final_states = { 1, 0 },
  };

转换函数表示为状态（行）和事件（列）的矩阵，因此函数 *f* : *X* x *E* -> *X* 可以在 O(1) 时间内解决。例如：

  next_state = automaton_wip.function[curr_state][event];

Graphviz .dot 格式
--------------------

Graphviz 开源工具可以使用（文本）DOT 语言作为源代码生成自动机的图形表示。
DOT 格式被广泛使用并且可以转换为许多其他格式。
例如，这是 'wip' 模型的 DOT 表示：

  digraph state_automaton {
        {node [shape = circle] "非抢占式"};
        {node [shape = plaintext, style=invis, label=""] "__init_preemptive"};
        {node [shape = doublecircle] "抢占式"};
        {node [shape = circle] "抢占式"};
        "__init_preemptive" -> "抢占式";
        "非抢占式" [label = "非抢占式"];
        "非抢占式" -> "非抢占式" [ label = "调度唤醒" ];
        "非抢占式" -> "抢占式" [ label = "启用抢占" ];
        "抢占式" [label = "抢占式"];
        "抢占式" -> "非抢占式" [ label = "禁用抢占" ];
        { rank = min ;
                "__init_preemptive";
                "抢占式";
        }
  }

此 DOT 格式可以使用 dot 工具转换为位图或矢量图像，或者使用 graph-easy 转换为 ASCII 艺术图像。例如：

  $ dot -Tsvg -o wip.svg wip.dot
  $ graph-easy wip.dot > wip.txt

dot2c
-----

dot2c 是一个工具，可以解析包含自动机的 .dot 文件（如上例所示），并将其自动转换为 C 表示法。
例如，将前面的 'wip' 模型保存到名为 'wip.dot' 的文件中，以下命令会将 .dot 文件转换为 C 表示法（如前所述），并输出到 'wip.h' 文件中：

  $ dot2c wip.dot > wip.h

'wip.h' 文件的内容就是“C语言中的确定性自动机”部分的代码样例。

备注
-------

自动机的形式化允许以多种适合不同应用/用户的格式建模离散事件系统（DES）。
例如，使用集合论的正式描述更适合自动机操作，而图形格式更适合人类解释；计算机语言则适用于机器执行。
参考文献
----------

许多教科书都涵盖了自动机的形式化理论。简要介绍可参见：

  O'Regan, Gerard. 《软件工程简明指南》. Springer, Cham, 2017

对于详细的描述，包括操作和离散事件系统（DES）的应用，可参见：

  Cassandras, Christos G., 和 Stephane Lafortune 主编. 《离散事件系统导论》. Boston, MA: Springer US, 2008

关于内核中的 C 表示法，可参见：

  De Oliveira, Daniel Bristot; Cucinotta, Tommaso; De Oliveira, Romulo Silva. 《Linux 内核的高效形式验证》. 在：国际软件工程与形式方法会议. Springer, Cham, 2019. 第 315-332 页
