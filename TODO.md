1. Use get_output_panel to dispaly help strings/object infos 
2. Add support for creating/renaming notebooks
3. Add an option of saving a backup copy of notebook json file (use git to have all copies?):
    - For now it is possible to use inb_open_as_ipynb command
4. Support for non-"python code" cells
5. Correctly handle 'dead' message from the kernel
6. Completion should work in the middle of the string: "a = x." not only for "x."
7. Use scopes to highlight python code only inside input cells
