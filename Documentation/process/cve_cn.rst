== Common Vulnerabilities and Exposures (CVEs) ==

Common Vulnerabilities and Exposures (CVE®) 编号被开发为一种明确的方式，用于识别、定义和编目公开披露的安全漏洞。随着时间的推移，这些编号对于内核项目而言用处逐渐减少，并且经常被不适当地分配给不恰当的问题。正因为如此，内核开发社区倾向于避免使用它们。然而，持续要求分配 CVE 及其他形式安全标识符的压力以及内核社区之外个人和公司的滥用行为表明，内核社区应该对这些分配有控制权。
Linux 内核开发者团队确实有能力为潜在的 Linux 内核安全问题分配 CVE 编号。这种分配独立于 [正常的 Linux 内核安全漏洞报告流程](../process/security-bugs)。
所有为 Linux 内核分配的 CVE 编号列表可以在 [linux-cve 邮件列表](https://lore.kernel.org/linux-cve-announce/) 的存档中找到。为了获得已分配的 CVE 编号的通知，请[订阅该邮件列表](https://subspace.kernel.org/subscribing.html)。

== 流程 ==

作为正常稳定版本发布过程的一部分，负责 CVE 编号分配的开发者会识别出可能涉及安全问题的内核变更，并自动为其分配 CVE 编号。这些分配会在 linux-cve-announce 邮件列表中频繁地公布。
需要注意的是，由于 Linux 内核在系统中的层级，几乎任何漏洞都可能被利用来破坏内核的安全性，但在修复漏洞时，其可利用的可能性往往并不明显。因此，CVE 分配团队非常谨慎，会对他们识别到的任何补丁分配 CVE 编号。这解释了为何 Linux 内核团队发布的 CVE 数量看似较多。
如果 CVE 分配团队遗漏了某个用户认为应分配 CVE 编号的具体修复项，请通过 <cve@kernel.org> 发送电子邮件给团队，他们会与您合作处理。请注意，不应将任何潜在的安全问题发送到此别名地址；它仅用于已存在于发布的内核树中的修复项的 CVE 分配。如果您发现未修复的安全问题，请遵循 [正常的 Linux 内核安全漏洞报告流程](../process/security-bugs)。
对于未修复的 Linux 内核安全问题，不会自动分配 CVE 编号；只有当修复可用并应用于稳定的内核树后才会自动分配，并且会根据原始修复的 Git 提交 ID 进行跟踪。如果任何人希望在问题得到解决前分配 CVE 编号，请联系内核 CVE 分配团队 <cve@kernel.org> 以从他们的预留标识符批次中获取标识符。
对于不在当前由 Stable/LTS 内核团队积极支持的内核版本中发现的任何问题，都不会分配 CVE 编号。当前支持的内核分支列表可以在 [https://kernel.org/releases.html](https://kernel.org/releases.html) 找到。

== 已分配 CVE 的争议 ==

对于特定内核变更所分配的 CVE 的争议或修改权限仅属于受其影响的相关子系统的维护者。这一原则确保了漏洞报告的高度准确性和责任性。只有那些对该子系统具有深厚专业知识和深入了解的人才能有效评估报告漏洞的有效性和范围，并确定其适当的 CVE 标识。任何试图在指定权限之外修改或争议 CVE 的行为都可能导致混乱、不准确的报告，最终可能导致系统的妥协。

== 无效的 CVEs ==

如果在 Linux 内核中发现的安全问题是由于某个 Linux 发行版所做的更改或由于发行版支持的内核版本不再属于 kernel.org 支持的版本，则 Linux 内核 CVE 团队无法为此分配 CVE，必须向该 Linux 发行版请求。
对于处于活动支持状态的内核版本，除内核 CVE 分配团队外的任何团体所分配的针对 Linux 内核的 CVE 不应被视为有效的 CVE。请通知内核 CVE 分配团队 <cve@kernel.org>，以便他们能够通过 CNA 纠正流程使此类条目失效。
特定CVE的适用性
=================

由于Linux内核可以以多种不同的方式使用，并且外部用户可以通过许多不同的方式访问它，或者根本无法访问，因此任何特定CVE的适用性取决于Linux用户自行判断，而不是由CVE分配团队来决定。请不要联系我们试图确定任何特定CVE的适用性。

此外，由于源代码树非常庞大，而任何一个系统只使用其中的一小部分，所有Linux用户都应该意识到，大量已分配的CVE可能与他们的系统无关。

简而言之，我们不了解您的具体应用场景，也不知道您使用了内核的哪些部分，因此我们无法判断某个特定CVE是否对您的系统相关。

一如既往，最好是采纳所有发布的内核更新，因为这些更新是由社区成员作为一个整体进行测试的，而不是作为单独挑选的个别更新。同时需要注意的是，对于许多问题，解决办法往往不是通过单一的更改实现的，而是通过多个修复的累积效果。理想情况下，所有问题的所有修复都会被分配CVE，但有时我们会遗漏一些修复，因此可以假设某些没有分配CVE的更改可能是相关的。
