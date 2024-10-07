修改补丁
========

如果你是子系统或分支的维护者，有时你需要稍微修改收到的补丁以便合并，因为你的代码树和提交者的代码树并不完全相同。如果你严格遵守开发者来源证书中的规则（c），你应该要求提交者重新生成补丁，但这完全是浪费时间和精力。规则（b）允许你调整代码，但之后将错误归咎于某个提交者是非常不礼貌的。为了解决这个问题，建议你在最后一个“Signed-off-by”头和你的签名之间添加一行，说明你所做的修改。虽然这不是强制性的，但在描述前加上你的邮件地址和/或名字，并用方括号括起来，这样就足以表明你是最后时刻修改的责任人。例如：

```
       Signed-off-by: Random J Developer <random@developer.example.org>
       [lucky@maintainer.example.org: struct foo moved from foo.c to foo.h]
       Signed-off-by: Lucky K Maintainer <lucky@maintainer.example.org>
```

这种做法特别有助于你维护稳定分支时，同时赞扬作者、跟踪修改、合并修复并保护提交者免受投诉。请注意，在任何情况下，你都不能更改作者的身份（即From头），因为这是出现在变更日志中的身份。
对回退者的特别说明：在提交信息的顶部（主题行之后）插入补丁来源的信息是一种常见且有用的做法，便于追踪。例如，在3.x-stable版本中我们看到如下内容：

```
Date:   Tue Oct 7 07:26:38 2014 -0400

    libata: Un-break ATA blacklist

    commit 1c40279960bcd7d52dbdf1d466b20d24b99176c8 upstream
```

而在旧内核中回退补丁后可能会出现如下内容：

```
Date:   Tue May 13 22:12:27 2008 +0200

    wireless, airo: waitbusy() won't delay

    [backport of 2.6 commit b7acbdfbd1f277c1eb23f344f899cfa4cd0bf36a]
```

无论采用何种格式，这些信息都为追踪你的代码树以及试图解决你代码树中bug的人提供了宝贵的帮助。
