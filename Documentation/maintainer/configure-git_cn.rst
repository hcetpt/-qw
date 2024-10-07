配置 Git
===============

本章描述了维护者级别的 Git 配置。
在拉取请求中使用的带标签分支（参见 `Documentation/maintainer/pull-requests.rst`）应使用开发者的公共 GPG 密钥进行签名。可以通过向 `git tag` 传递 ``-u <key-id>`` 来创建带签名的标签。然而，由于你通常会在项目中使用同一个密钥，因此可以在配置中设置它，并使用 ``-s`` 标志。要设置默认的 ``key-id`` ，可以使用：

```shell
git config user.signingkey "keyname"
```

或者手动编辑你的 ``.git/config`` 或 ``~/.gitconfig`` 文件：

```shell
[user]
	name = Jane Developer
	email = jd@domain.org
	signingkey = jd@domain.org
```

你可能需要告诉 ``git`` 使用 ``gpg2`` ：

```shell
[gpg]
	program = /path/to/gpg2
```

你还可以告诉 ``gpg`` 使用哪个 ``tty`` （添加到你的 shell 配置文件中）：

```shell
export GPG_TTY=$(tty)
```

创建指向 lore.kernel.org 的提交链接
----------------------------------------

网站 https://lore.kernel.org 是所有与内核开发相关或影响内核开发的邮件列表存档的大仓库。将补丁存档存储在这里是一种推荐的做法。当维护者将一个补丁应用到子系统树时，提供一个指向 lore 存档的引用链接是一个好主意，这样浏览提交历史的人可以找到相关的讨论和某个更改背后的理由。链接标签看起来像这样：

```shell
Link: https://lore.kernel.org/r/<message-id>
```

可以通过在你的 Git 中添加以下钩子来自动完成这一过程：

```shell
$ git config am.messageid true
$ cat >.git/hooks/applypatch-msg <<'EOF'
#!/bin/sh
. git-sh-setup
perl -pi -e 's|^Message-I[dD]:\s*<?([^>]+)>?$|Link: https://lore.kernel.org/r/$1|g;' "$1"
test -x "$GIT_DIR/hooks/commit-msg" &&
  exec "$GIT_DIR/hooks/commit-msg" ${1+"$@"}
:
EOF
$ chmod a+x .git/hooks/applypatch-msg
```
