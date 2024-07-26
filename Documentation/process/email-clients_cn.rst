Linux下的电子邮件客户端信息
============================

Git
---

如今大多数开发者使用`git send-email`而不是常规的电子邮件客户端。这个命令的手册页面非常好。在接收端，维护者使用`git am`来应用补丁。
如果你是`git`的新手，那么请先将你的第一个补丁发送给自己。保存它为原始文本，包括所有的头部信息。运行`git am raw_email.txt`，然后通过`git log`审查更改日志。当这一切都能正常工作时，再将补丁发送到合适的邮件列表。

通用设置
-------------------

针对Linux内核的补丁是通过电子邮件提交的，最好是以邮件正文中的内联文本形式。一些维护者接受附件，但如果使用附件，则附件的内容类型应该是`text/plain`。然而，通常不推荐使用附件，因为这会使得在补丁审核过程中引用补丁的部分内容变得更加困难。

强烈建议你在邮件正文中使用纯文本格式，无论是补丁还是其他邮件都一样。https://useplaintext.email 可能对你有用，它可以提供如何配置你首选的电子邮件客户端的信息，同时也列出了推荐的电子邮件客户端，如果你还没有偏好选择的话。

用于Linux内核补丁的电子邮件客户端应该原样发送补丁文本。例如，它们不应该修改或删除制表符或空格，即使是在行首或行尾。

不要以`format=flowed`的形式发送补丁。这可能会导致意外且不需要的换行。

不要让你的电子邮件客户端为你自动换行。

这也可能破坏你的补丁。

电子邮件客户端不应该修改文本的字符集编码。

通过电子邮件发送的补丁应该只使用ASCII或UTF-8编码。
如果你将电子邮件客户端配置为使用UTF-8编码发送邮件，
你可以避免一些可能的字符集问题。
电子邮件客户端应当生成并维护“References:”或“In-Reply-To:”这样的头部信息，
以确保邮件线程不会被破坏。
复制粘贴（或剪切粘贴）通常对补丁不起作用，
因为制表符会被转换为空格。使用xclipboard、xclip和/或xcutsel可能会起作用，但最好是自己测试一下或者干脆避免复制粘贴操作。
在包含补丁的邮件中不要使用PGP/GPG签名，
这会破坏许多读取并应用补丁的脚本。（这个问题应该是可以修复的。）

在向Linux邮件列表发送补丁之前，最好先给自己发一个补丁，保存收到的消息，并成功地用‘patch’命令应用它。

一些电子邮件客户端（MUA）提示
-----------------------------------

下面是一些针对编辑和发送Linux内核补丁的具体MUA配置提示。这些并不是完整的软件包配置指南。

术语解释：

- TUI = 基于文本的用户界面
- GUI = 图形用户界面

Alpine（TUI）
************

配置选项：

在“发送偏好设置”部分：

- “不发送流式文本”必须是“启用”的状态
- “发送前删除空白”必须是“禁用”的状态

在撰写消息时，光标应放置在补丁出现的位置，然后按<kbd>CTRL-R</kbd>键来指定要插入到消息中的补丁文件。
Claws Mail（GUI）
*****************

可用。有些人成功地使用这个工具处理补丁。
要插入补丁，请使用“消息->插入文件”（<kbd>CTRL-I</kbd>）功能或外部编辑器。
如果需要在 Claws 的编辑窗口中编辑插入的补丁，则应禁用
“自动换行”功能：
在 :menuselection:`配置-->首选项-->撰写-->换行` 中将其关闭。
#### Evolution（图形用户界面）
一些人成功地使用 Evolution 来处理补丁。
撰写邮件时，请选择：预格式化
从 :menuselection:`格式-->段落样式-->预格式化`（:kbd:`CTRL-7`），
或工具栏。

然后使用：
:menuselection:`插入-->文本文件...`（:kbd:`ALT-N x`）
来插入补丁。
您也可以使用 `diff -Nru old.c new.c | xclip`，选择
:menuselection:`预格式化`，然后通过中间鼠标键进行粘贴。
#### Kmail（图形用户界面）
一些人成功地使用 Kmail 处理补丁。
默认不以 HTML 格式撰写邮件是合适的；不要启用它。
撰写邮件时，在选项中取消选中“自动换行”。唯一的缺点是，
你在邮件中输入的任何文本都不会自动换行，因此你需要手动对补丁前的文本进行换行。最简便的方法是在开启自动换行的情况下撰写你的邮件，然后保存为草稿。当你再次从草稿箱中打开时，文本已经被硬换行，此时可以取消选中“自动换行”，而不会影响已有的换行。
在邮件底部，插入常用的补丁分隔符，即在插入补丁之前放置三个破折号（``---``）。
然后从 :menuselection:`消息` 菜单项中，选择
:menuselection:`插入文件` 并选择你的补丁文件。
另外，你还可以自定义消息创建工具栏菜单，并将
:menuselection:`插入文件` 图标放在那里。
使作曲窗口足够宽，以确保没有行被换行。截至 KMail 1.13.5（KDE 4.5.4），如果在作曲窗口中出现了换行，KMail 在发送电子邮件时会应用文字换行。仅仅在选项菜单中禁用文字换行是不够的。因此，如果你的补丁文件包含非常长的行，在发送电子邮件之前必须将作曲窗口设置得非常宽。详情请见：https://bugs.kde.org/show_bug.cgi?id=174034

你可以安全地使用 GPG 签名附件，但对于补丁来说，内嵌文本更受欢迎，因此不要对它们进行 GPG 签名。对已作为内嵌文本插入的补丁进行签名会使它们难以从其 7 位编码中提取出来。如果你确实需要将补丁作为附件发送而不是作为文本内嵌，请右键点击附件并选择“属性”，然后突出显示“建议自动显示”来使附件内嵌，从而提高可读性。
当保存作为内嵌文本发送的补丁时，从邮件列表窗格中选择包含补丁的邮件，右键点击并选择“另存为”。如果正确编写了邮件，则可以不加修改地使用整个邮件作为补丁。邮件默认以只对用户可读写的方式保存，因此如果你将它们复制到其他地方，则需要使用 chmod 命令使其对组和世界可读。

Lotus Notes（图形用户界面）
******************************

远离它

IBM Verse（网页图形用户界面）
********************************

参见 Lotus Notes

Mutt（文本用户界面）
************************

许多 Linux 开发者使用 `mutt` ，所以它应该工作得很好。
Mutt 不自带编辑器，所以无论你使用什么编辑器都应该确保没有自动换行。大多数编辑器都有一个“插入文件”的选项，该选项会原样插入文件内容。
要使用 `vim` 和 mutt，请执行如下设置：

  set editor="vi"

如果使用 xclip，请输入命令：

  :set paste

在中间按钮点击或 Shift 插入前，或者使用：

  :r filename

如果你想将补丁内嵌在邮件中。
(a)ttach 可以正常工作而不需要 `set paste` 指令。
你也可以使用 `git format-patch` 生成补丁，然后使用 Mutt 发送它们：

    $ mutt -H 0001-some-bug-fix.patch

配置选项：

默认设置下应该可以正常工作。
然而，将 `send_charset` 设置为如下是一个好主意：

  set send_charset="us-ascii:utf-8"

Mutt 高度可定制。以下是一个最小配置示例，用于通过 Gmail 使用 Mutt 发送补丁：

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
  set editor = `echo $EDITOR`
  set edit_headers = yes  # 在编辑时查看头部信息
  set charset = UTF-8     # $LANG 的值；也是 send_charset 的备选设置
  # 发件人、电子邮件地址和署名行必须匹配
  unset use_domain        # 因为 joe@localhost 确实很尴尬
  set realname = "YOUR NAME"
  set from = "username@gmail.com"
  set use_from = yes

Mutt 文档包含更多信息：

    https://gitlab.com/muttmua/mutt/-/wikis/UseCases/Gmail

    http://www.mutt.org/doc/manual/

Pine（文本用户界面）
**********

Pine 过去存在一些空白字符截断的问题，但现在这些问题应该都已修复。
如果可能的话，请使用 Alpine（Pine 的后继者）。
配置选项：

- 对于较新版本，需要使用 ``quell-flowed-text``
- 需要使用 ``no-strip-whitespace-before-send`` 选项

Sylpheed（图形用户界面）
**************

- 对于内联文本处理得很好（或使用附件）
- 允许使用外部编辑器
- 在大型文件夹中运行缓慢
- 不支持在非 SSL 连接上进行 TLS SMTP 认证
- 在撰写窗口中有一个有用的标尺栏
- 添加联系人到通讯录时不能正确解析显示名称

Thunderbird（图形用户界面）
*****************

Thunderbird 类似于 Outlook，并且倾向于破坏文本格式，但有一些方法可以使其表现得更好。
进行这些修改之后，包括安装扩展程序，你需要重启 Thunderbird。
允许使用外部编辑器：

对于 Thunderbird 和补丁来说，最简便的方法是使用扩展程序来打开您喜爱的外部编辑器。
以下是一些能够实现这一功能的示例扩展：
- “External Editor Revived”

    https://github.com/Frederick888/external-editor-revived

    https://addons.thunderbird.net/en-GB/thunderbird/addon/external-editor-revived/

    需要安装一个“原生消息主机”。请阅读此wiki页面以获取更多信息： 
    https://github.com/Frederick888/external-editor-revived/wiki

- “External Editor”

    https://github.com/exteditor/exteditor

    您需要下载并安装该扩展程序，然后打开
    :menuselection:`撰写` 窗口，并通过
    :menuselection:`视图-->工具栏-->自定义...` 添加一个按钮，
    当您希望使用外部编辑器时只需点击新添加的按钮即可。
请注意，“External Editor”要求您的编辑器不能分叉，换句话说，在关闭前编辑器不能返回。
您可能需要向编辑器传递额外的标志或更改其设置。特别是如果您使用的是gvim，则必须通过在
:menuselection:`外部编辑器` 设置中的文本编辑器字段输入 ``/usr/bin/gvim --nofork``（如果二进制文件位于 ``/usr/bin`` 文件夹中）来为gvim传递 `-f` 选项。
如果您使用的是其他编辑器，请参阅其手册了解如何执行此操作。

为了改进内部编辑器的功能，请执行以下操作：

- 编辑您的 Thunderbird 配置设置，确保不使用 ``format=flowed``！
  在主窗口中找到主下拉菜单按钮，然后选择
  :menuselection:`主菜单-->首选项-->常规-->配置编辑器...` 以打开 Thunderbird 的注册表编辑器。
- 将 ``mailnews.send_plaintext_flowed`` 设置为 ``false``

  - 将 ``mailnews.wraplength`` 从 ``72`` 更改为 ``0``

- 不要撰写 HTML 格式的邮件！在主窗口中选择
  :menuselection:`主菜单-->帐户设置-->youracc@server.something-->撰写与地址`，在那里您可以禁用“以 HTML 格式撰写邮件”的选项。
- 只以纯文本形式打开邮件！在主窗口中选择
  :menuselection:`主菜单-->视图-->作为正文显示消息-->纯文本`！

TkRat（图形用户界面）
**********************

可以使用。使用“插入文件...” 或外部编辑器。
Gmail（网页图形界面）
***************

不适用于发送补丁
Gmail 网页客户端会自动将制表符转换为空格
同时，它会在每 78 个字符处以 CRLF 样式换行
尽管使用外部编辑器可以解决制表符转空格的问题
另一个问题是 Gmail 会对包含非 ASCII 字符的任何邮件进行 base64 编码。这包括像欧洲名字这样的内容
HacKerMaiL（文本用户界面）
****************

HacKerMaiL（hkml）是一个基于公共邮箱的简单邮件管理工具，不需要订阅邮件列表。它由 DAMON 的维护者开发和维护，并旨在支持 DAMON 和通用内核子系统的简单开发工作流程。详情请参阅 README（[https://github.com/sjp38/hackermail/blob/master/README.md](https://github.com/sjp38/hackermail/blob/master/README.md)）。
