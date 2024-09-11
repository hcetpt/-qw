====== 键盘通知器 ======

可以使用 `register_keyboard_notifier` 来在键盘事件发生时接收回调（详见 `kbd_keycode()` 函数的细节）。传递的结构体是 `keyboard_notifier_param`（见 `<linux/keyboard.h>`）：

- `'vc'` 始终提供与该键盘事件相关的虚拟控制台（VC）；
- `'down'` 在按键按下事件中为 1，在按键释放事件中为 0；
- `'shift'` 是当前的修饰键状态，掩码位索引为 KG_*；
- `'ledstate'` 是当前的 LED 状态；
- `'value'` 取决于事件类型：
  - `KBD_KEYCODE` 事件总是在其他事件之前发送，值为键码；
  - `KBD_UNBOUND_KEYCODE` 事件会在键码未绑定到一个键符时发送，值为键码；
  - `KBD_UNICODE` 事件会在键码到键符的转换产生一个 Unicode 字符时发送，值为 Unicode 值；
  - `KBD_KEYSYM` 事件会在键码到键符的转换产生一个非 Unicode 字符时发送，值为键符；
  - `KBD_POST_KEYSYM` 事件会在处理非 Unicode 键符之后发送。这允许检查最终的 LED 状态等。

对于除了最后一个以外的所有类型的事件，回调函数可以返回 `NOTIFY_STOP` 来“吞掉”事件：通知循环将停止，并且键盘事件会被丢弃。

在一个简单的 C 代码片段中，我们有：

```c
    kbd_keycode(keycode) {
        ..
```
```c
params.value = keycode;
if (notifier_call_chain(KBD_KEYCODE, &params) == NOTIFY_STOP) 
    || !bound) {
    notifier_call_chain(KBD_UNBOUND_KEYCODE, &params);
    return;
}

if (unicode) {
    params.value = unicode;
    if (notifier_call_chain(KBD_UNICODE, &params) == NOTIFY_STOP)
        return;
    emit unicode;
    return;
}

params.value = keysym;
if (notifier_call_chain(KBD_KEYSYM, &params) == NOTIFY_STOP)
    return;
apply keysym;
notifier_call_chain(KBD_POST_KEYSYM, &params);
}

.. note:: 此通知器通常在中断上下文中调用
```

注释：
- `params.value = keycode;`：将 `keycode` 的值赋给 `params.value`。
- `notifier_call_chain(KBD_KEYCODE, &params)`：调用通知链 `KBD_KEYCODE` 并传递参数 `params`。
- 如果返回值为 `NOTIFY_STOP` 或者 `bound` 为假，则调用 `KBD_UNBOUND_KEYCODE` 通知链，并返回。
- 如果 `unicode` 不为空，则将 `unicode` 的值赋给 `params.value`，并调用 `KBD_UNICODE` 通知链。如果返回值为 `NOTIFY_STOP`，则返回。否则发出 `unicode` 并返回。
- 否则将 `keysym` 的值赋给 `params.value`，并调用 `KBD_KEYSYM` 通知链。如果返回值为 `NOTIFY_STOP`，则返回。否则应用 `keysym`，并调用 `KBD_POST_KEYSYM` 通知链。

注意：此通知器通常在中断上下文中调用。
