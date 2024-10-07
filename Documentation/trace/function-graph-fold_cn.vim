```vim
" 启用 ftrace 函数图跟踪的折叠功能
"
" 使用方法：在查看函数图跟踪时，使用 :source 命令加载此文件，或者使用 Vim 的
" -S 选项从命令行与跟踪文件一起加载。然后可以使用 Vim 的常规折叠命令，
" 如 "za"，来打开和关闭嵌套函数。当关闭时，折叠会显示调用所花费的总时间，
" 这通常会出现在闭合大括号所在的行上。折叠的函数不包括 finish_task_switch()，
" 因此即使在上下文切换期间，折叠功能依然保持相对合理。
"
" 注意：这几乎肯定只适用于单个 CPU 的跟踪（例如：trace-cmd report --cpu 1）

function! FunctionGraphFoldExpr(lnum)
  let line = getline(a:lnum)
  if line[-1:] == '{'
    if line =~ 'finish_task_switch() {$'
      return '>1'
    endif
    return 'a1'
  elseif line[-1:] == '}'
    return 's1'
  else
    return '='
  endif
endfunction

function! FunctionGraphFoldText()
  let s = split(getline(v:foldstart), '|', 1)
  if getline(v:foldend+1) =~ 'finish_task_switch() {$'
    let s[2] = ' task switch  '
  else
    let e = split(getline(v:foldend), '|', 1)
    let s[2] = e[2]
  endif
  return join(s, '|')
endfunction

setlocal foldexpr=FunctionGraphFoldExpr(v:lnum)
setlocal foldtext=FunctionGraphFoldText()
setlocal foldcolumn=12
setlocal foldmethod=expr
```

这段代码为 Vim 配置了 ftrace 函数图跟踪的折叠功能，并提供了详细的说明和使用方法。
