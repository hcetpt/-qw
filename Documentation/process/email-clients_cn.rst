### Linux 邮件客户端信息

#### Git
---

如今，大多数开发人员使用 `git send-email` 而不是传统的邮件客户端。这个命令的手册页面非常详细。在接收端，维护者使用 `git am` 来应用补丁。

如果你是 `git` 的新手，请将你的第一个补丁发送给自己。保存为原始文本，包括所有头部信息。运行 `git am raw_email.txt`，然后通过 `git log` 查看提交日志。当这一切都正常工作时，再将补丁发送到相应的邮件列表。

#### 通用设置
---

Linux 内核的补丁通过电子邮件提交，最好是作为邮件正文中的内联文本。一些维护者接受附件，但这些附件的内容类型应该是 `text/plain`。然而，一般不建议使用附件，因为这会使得在补丁审查过程中引用补丁的部分内容更加困难。

强烈推荐你在邮件正文中使用纯文本，无论是补丁还是其他邮件。https://useplaintext.email 可能对你配置首选的邮件客户端有帮助，并且列出了推荐的邮件客户端，供你选择。

用于 Linux 内核补丁的邮件客户端应该原样发送补丁文本。例如，它们不应该修改或删除制表符或空格，即使是在行首或行尾。

不要发送带有 `format=flowed` 的补丁。这可能会导致意外且不需要的换行。

不要让邮件客户端为你自动换行。这也可能会破坏你的补丁。

邮件客户端不应修改文本的字符集编码。电子邮件补丁应仅使用 ASCII 或 UTF-8 编码。
如果你将电子邮件客户端配置为使用 UTF-8 编码发送邮件，可以避免一些可能的字符集问题。
电子邮件客户端应生成并维护 "References:" 或 "In-Reply-To:" 标头，以确保邮件线程不会中断。
复制粘贴（或剪切粘贴）通常对补丁不起作用，因为制表符会被转换为空格。使用 xclipboard、xclip 和/或 xcutsel 可能会起作用，但最好自己测试一下，或者避免使用复制粘贴。
不要在包含补丁的邮件中使用 PGP/GPG 签名。
这会破坏许多读取和应用补丁的脚本。（这个问题应该是可以修复的。）

在将补丁发送到 Linux 邮件列表之前，最好先将补丁发送给自己，保存收到的消息，并成功地用 'patch' 命令应用它。

一些电子邮件客户端（MUA）提示
-----------------------------------

以下是一些用于编辑和发送 Linux 内核补丁的具体 MUA 配置提示。这些并不是完整的软件包配置指南。

术语说明：

- TUI = 文本用户界面
- GUI = 图形用户界面

Alpine（TUI）
************

配置选项：

在 :menuselection:`发送偏好设置` 部分：

- :menuselection:`不发送流式文本` 必须是“启用”状态
- :menuselection:`发送前删除空白` 必须是“禁用”状态

在撰写消息时，光标应放置在补丁出现的位置，然后按 :kbd:`CTRL-R` 键可以选择要插入消息中的补丁文件。

Claws Mail（GUI）
****************

有效。有些人成功地使用它来发送补丁。
要插入一个补丁，请使用 :menuselection:`消息-->插入文件` (:kbd:`CTRL-I`) 或外部编辑器。
如果插入的补丁需要在 Claws 的编辑窗口中进行编辑，
应禁用“自动换行”功能：
:menuselection:`配置-->首选项-->编辑-->换行`

Evolution（图形界面）
***************

有些人成功地使用 Evolution 来处理补丁。
在撰写邮件时选择：预格式化
从 :menuselection:`格式-->段落样式-->预格式化` (:kbd:`CTRL-7`)，
或者工具栏。

然后使用：
:menuselection:`插入-->文本文件...` (:kbd:`ALT-N x`)
来插入补丁。
你也可以通过 `diff -Nru old.c new.c | xclip`，选择
:menuselection:`预格式化`，然后用鼠标中键粘贴。

Kmail（图形界面）
***********

有些人成功地使用 Kmail 处理补丁。
默认不以 HTML 格式撰写邮件是合适的；不要启用它。
在撰写电子邮件时，在选项中取消选中“自动换行”。唯一的缺点是你输入的任何文本都不会自动换行，因此你需要在插入补丁前手动换行。最简单的方法是在启用自动换行的情况下撰写邮件，然后将其保存为草稿。当你再次从草稿箱中打开它时，文本已经硬换行了，此时你可以取消选中“自动换行”而不丢失现有的换行。

在邮件底部插入常用的补丁分隔符，然后再插入你的补丁：三个连字符（``---``）。
然后从 :menuselection:`消息` 菜单项中选择 :menuselection:`插入文件` 并选择你的补丁文件。
作为额外的好处，你可以自定义消息创建工具栏菜单，并将 :menuselection:`插入文件` 图标放在那里。
使作曲窗口足够宽，以确保没有行换行。截至 KMail 1.13.5（KDE 4.5.4），如果作曲窗口中的行发生换行，KMail 在发送电子邮件时将应用自动换行。在选项菜单中禁用自动换行是不够的。因此，如果你的补丁包含非常长的行，在发送电子邮件之前必须使作曲窗口足够宽。详情见：https://bugs.kde.org/show_bug.cgi?id=174034

你可以安全地使用 GPG 签名附件，但对于补丁，建议内嵌文本，因此不要对它们进行 GPG 签名。对作为内嵌文本插入的补丁进行签名会使它们难以从其 7 位编码中提取。如果你确实需要将补丁作为附件发送而不是作为文本内嵌，请右键单击附件并选择 :menuselection:`属性`，然后突出显示 :menuselection:`建议自动显示` 以使附件内嵌以便于查看。当保存作为内嵌文本发送的补丁时，请从邮件列表窗格中选择包含补丁的邮件，右键单击并选择 :menuselection:`另存为`。如果邮件正确组成，可以使用整个未修改的邮件作为补丁。邮件仅以用户可读写的方式保存，因此如果你将其复制到其他地方，则需要使用 `chmod` 使其对组和世界可读。

Lotus Notes (GUI)
*****************

远离它

IBM Verse (Web GUI)
*******************

参见 Lotus Notes

Mutt (TUI)
**********

许多 Linux 开发者使用 `mutt`，所以它应该工作得很好。Mutt 不自带编辑器，因此你使用的任何编辑器都应确保没有自动换行。大多数编辑器都有一个 :menuselection:`插入文件` 选项，可以原样插入文件内容。要使用 `vim` 与 Mutt 配合，请执行以下操作：

  set editor="vi"

如果使用 xclip，请输入命令：

  :set paste

在中键点击或 Shift 插入之前，或者使用：

  :r filename

如果你想内嵌补丁的话。（a）ttach 在不使用 `set paste` 的情况下也能正常工作。

你也可以使用 `git format-patch` 生成补丁，然后使用 Mutt 发送它们：

    $ mutt -H 0001-some-bug-fix.patch

配置选项：

默认设置下应该可以正常工作。
然而，将 ``send_charset`` 设置为以下内容是一个好主意：

  set send_charset="us-ascii:utf-8"

Mutt 非常可定制。以下是一个最小配置示例，用于通过 Gmail 使用 Mutt 发送补丁：

  # .muttrc
  # ================  IMAP ====================
  set imap_user = 'yourusername@gmail.com'
  set imap_pass = 'yourpassword'
  set spoolfile = imaps://imap.gmail.com/INBOX
  set folder = imaps://imap.gmail.com/
  set record="imaps://imap.gmail.com/[Gmail]/Sent Mail"
  set postponed="imaps://imap.gmail.com/[Gmail]/Drafts"
  set mbox="imaps://imap.gmail.com/[Gmail]/All Mail"

  # ================  SMTP  ====================
  set smtp_url = "smtp://username@smtp.gmail.com:587/"
  set smtp_pass = $imap_pass
  set ssl_force_tls = yes # 要求加密连接

  # ================  Composition  ====================
  set editor = `echo \$EDITOR`
  set edit_headers = yes  # 在编辑时查看头部信息
  set charset = UTF-8     # $LANG 的值；也是 send_charset 的备选
  # 发件人、电子邮件地址和签名行必须匹配
  unset use_domain        # 因为 joe@localhost 真的是太尴尬了
  set realname = "YOUR NAME"
  set from = "username@gmail.com"
  set use_from = yes

Mutt 的文档包含更多信息：

    https://gitlab.com/muttmua/mutt/-/wikis/UseCases/Gmail

    http://www.mutt.org/doc/manual/

Pine（文本界面）
**********

Pine 过去有一些空白字符截断问题，但这些问题现在应该都已经修复了。
如果可以的话，请使用 Alpine（Pine 的继任者）。
配置选项：

- ``quell-flowed-text`` 对于较新版本是必需的
- ``no-strip-whitespace-before-send`` 选项是必需的

Sylpheed（图形界面）
**************

- 在内联文本方面表现良好（或使用附件）
- 允许使用外部编辑器
- 在处理大型文件夹时速度较慢
- 不会在非 SSL 连接上进行 TLS SMTP 认证
- 在撰写窗口中有一个有用的标尺栏
- 添加地址到地址簿时不正确地理解显示名称

Thunderbird（图形界面）
*****************

Thunderbird 是一个类似 Outlook 的程序，喜欢破坏文本，但有办法使其正常工作。
在进行这些修改之后，包括安装扩展插件，你需要重启 Thunderbird。
允许使用外部编辑器：

对于 Thunderbird 和补丁，最简单的方法是使用扩展程序来打开您喜欢的外部编辑器。以下是一些能够实现这一功能的示例扩展：
- “External Editor Revived”

    https://github.com/Frederick888/external-editor-revived

    https://addons.thunderbird.net/en-GB/thunderbird/addon/external-editor-revived/

    它需要安装一个“原生消息主机”。请阅读这里的 Wiki：
    https://github.com/Frederick888/external-editor-revived/wiki

- “External Editor”

    https://github.com/exteditor/exteditor

    要实现这一点，请下载并安装扩展，然后打开 :menuselection:`compose` 窗口，使用 :menuselection:`View-->Toolbars-->Customize...` 添加一个按钮。当您希望使用外部编辑器时，只需点击这个新按钮即可。

请注意，“External Editor”要求您的编辑器不能分叉，换句话说，在关闭之前不能返回。您可能需要传递额外的标志或更改编辑器的设置。特别是如果您使用的是 gvim，则必须通过在 :menuselection:`external editor` 设置中的文本编辑字段中输入 ``/usr/bin/gvim --nofork``（如果二进制文件位于 ``/usr/bin`` 中）来传递 `-f` 选项。如果您使用的是其他编辑器，请查阅其手册以了解如何进行操作。

为了使内部编辑器更合理地工作，请执行以下操作：

- 编辑您的 Thunderbird 配置设置，使其不使用 ``format=flowed``！进入主窗口，找到主下拉菜单的按钮。
:menuselection:`Main Menu-->Preferences-->General-->Config Editor...` 以打开 Thunderbird 的注册表编辑器。
- 将 ``mailnews.send_plaintext_flowed`` 设置为 ``false``。

  - 将 ``mailnews.wraplength`` 从 ``72`` 更改为 ``0``。

- 不要撰写 HTML 格式的邮件！进入主窗口
:menuselection:`Main Menu-->Account Settings-->youracc@server.something-->Composition & Addressing`！在那里您可以禁用“以 HTML 格式撰写邮件”的选项。
- 只以纯文本格式打开邮件！进入主窗口
:menuselection:`Main Menu-->View-->Message Body As-->Plain Text`！

TkRat（图形界面）
**************

有效。使用“插入文件...”或外部编辑器。
Gmail（Web GUI）
**************

不适用于发送补丁
Gmail 网页客户端会自动将制表符转换为空格
同时，它会在每 78 个字符处使用 CRLF 风格的换行符进行换行
尽管制表符转空格的问题可以通过外部编辑器解决
另一个问题是 Gmail 会对包含非 ASCII 字符的任何消息进行 base64 编码。这包括像欧洲名字等
HacKerMaiL（TUI）
****************

HacKerMaiL（hkml）是一个基于公共邮箱的简单邮件管理工具，不需要订阅邮件列表。它由 DAMON 的维护者开发和维护，并旨在支持 DAMON 和通用内核子系统的简单开发工作流程。详情请参阅 README（https://github.com/sjp38/hackermail/blob/master/README.md）。
