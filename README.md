# Sublime IPython Notebook 
This is a Sublime Text 2 plugin that emulates IPython notebook interface inside Sublime. Currently it is possible to edit, execute and create cells. 

## Disclaimer
While the plugin looks stable so far and I am trying to preserve as much of the notebook data as possible, there are no guarantees that you data will be safe. Do not use it for the notebooks that contain valuable data without doing a backup.

## How to use
1. Connect to the notebook server using "Open IPython Notebook" command. Pick a notebook you want to open and it will open in a separate buffer.
2. Saving the notebook using ctrl+s or super+s is disable by default the plugin will become more stable. You can try to save notebook on your own risk using "Save IPython Notebook" command.
3. I am trying to maintain keyboard shortcuts from the web version of the notebook. Currently supported are:
    - shift+enter - execute current cell
    - ctrl+m, d - delete current cell
    - ctrl+m, a - add cell above current
    - ctrl+m, b - add cell below current

## Notes
1. You can use %pylab inline. You will not be able to see the plots, but they will be saved in the notebook and available when viewing it through the web interface.
2. Index of the cell is show instead of the prompt numbers are wrong right now.
3. A lot of other things are probably broken.
4. I am using websocket-client library from https://github.com/liris/websocket-client and (slightly patched) subset of the IPython. You do not have to install them separately. 
