# Sublime IPython Notebook 
This is a Sublime Text 3 plugin that emulates IPython notebook interface inside Sublime.

## Disclaimer
While the plugin looks stable so far and I am trying to preserve as much of the notebook data as possible, there are no guarantees that you data will be safe. Do not use it for the notebooks that contain valuable data without doing a backup.

## How to use
1. Connect to the notebook server using "Open IPython Notebook" command. Choose a notebook you want to open and it will open in a separate buffer.
2. I am trying to support keyboard shortcuts from the web version of the notebook. Currently you can use:
    - shift+enter - execute current cell
    - ctrl+enter - execute current cell inplace
    - ctrl+m, d - delete current cell
    - ctrl+m, a - add cell above current
    - ctrl+m, b - add cell below current
    - ctrl+m, n - select next cell
    - ctlr+m, p - select previous cell
    - ctrl+m, y - code cell
    - ctrl+m, m - markdown cell
    - ctrl+m, t - raw cell
    - ctrl+m, s - save notebook (ctrl+s and super+s will work too)

## Notes
1. You can use %pylab inline. You will not be able to see the plots, but they will be saved in the notebook and available when viewing it through the web interface.
2. I am using websocket-client library from https://github.com/liris/websocket-client and (slightly patched) subset of the IPython. You do not have to install them separately. 
3. ST3 port was contributed by [chirswl](https://github.com/chriswl)
4. Dark theme, support for password-protected servers and nicer last-used-server picker was contributed by [z-m-k](https://github.com/z-m-k)

## Vintage Mode
In Vintage mode, for the navigation keys to work as expected in IPython Notebook buffer, you need to modify some keybindings. Add the following to your `Key Bindings - User`.

1. Add a `context key` to `Shift+Enter` so you can run a cell with `Shift+Enter` in the command mode:

    ```
    { "keys": ["shift+enter"], "command": "set_motion", "args": {
        "motion": "move",
        "motion_args": {"by": "lines", "forward": true, "extend": true }},
        "context": [
            { "key": "setting.command_mode"},
            { "key": "setting.ipython_notebook", "operator": "equal", "operand": false },
            ]
    },
    ```
2. Command mode Up/Down navigation keys:

    ```
    { "keys": ["j"], "command": "set_motion", "args": {
        "motion": "move",
        "motion_args": {"by": "lines", "forward": true, "extend": true },
        "linewise": true },
        "context": [
            { "key": "setting.command_mode"},
            { "key": "setting.ipython_notebook", "operator": "equal", "operand": false },
            ]
    },
    
    {
        "keys": ["j"], "command": "inb_move_up",
        "context" : [
            { "key": "setting.command_mode"}
            { "key": "setting.ipython_notebook", "operator": "equal", "operand": true },
            { "key": "auto_complete_visible", "operator": "equal", "operand": false },
            ]
    },
    
    { "keys": ["k"], "command": "set_motion", "args": {
        "motion": "move",
        "motion_args": {"by": "lines", "forward": false, "extend": true },
        "linewise": true },
        "context": [
            { "key": "setting.command_mode"},
            { "key": "setting.ipython_notebook", "operator": "equal", "operand": false },
            ]
    },
    
    {
        "keys": ["k"], "command": "inb_move_down",
        "context" : [
            { "key": "setting.command_mode"},
            { "key": "setting.ipython_notebook", "operator": "equal", "operand": true },
            { "key": "auto_complete_visible", "operator": "equal", "operand": false },
            ]
    },
    ```
