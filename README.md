# Sublime IPython Notebook 
This is a Sublime Text 2 plugin that emulates IPython notebook interface inside Sublime.

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
    - ctrl+m, s - save notebook

## Notes
1. You can use %pylab inline. You will not be able to see the plots, but they will be saved in the notebook and available when viewing it through the web interface.
2. I am using websocket-client library from https://github.com/liris/websocket-client and (slightly patched) subset of the IPython. You do not have to install them separately. 
3. ST3 port was contributed by [chirswl](https://github.com/chriswl)
