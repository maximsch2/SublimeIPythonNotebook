- Alert if notebook was changed and offer to save before closing tab
- Better control for scrolling: if I have large ouput in the last cell that suddenly gets replaced, then my scroll position is screwed up
	- Maybe shuold keep scroll position fixed while changing output!
- Unclosed parenthesis still break highlighting (""" for python, and ' + " for R cells)
- Initial scroll position is bad for empty notebooks
- Support set_next_input
- Add an option of saving a backup copy of notebook json file (use git to have all copies?):
    - For now it is possible to use inb_open_as_ipynb command
- Support image preview in some external program

BUGS:

TODO for IPython 1.0

- support stdin input for %debug, raw_input and so on
