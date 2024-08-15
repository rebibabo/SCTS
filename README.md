# Environment
```
sudo apt-get install git graphviz graphviz-doc
pip install -r requirements.txt
```

# Introduction
SCTS is the abbreviation for **S**tyle **C**hange by **T**ree **S**itter, this tool aims to change a program to a specific style through tree-sitter.
Up till now, it can change C/C++/python with 148 rules, and it can also show the visual AST tree with graphviz and tokenize the code.
It will be continuous updated...

# How to use
This code is to define a class scts, the parametre is the language of the codes.
```
scts = SCTS('c')
```
After that, you can change the single file's style using code below, where the first parametre is the target style, this function will return the changed code and whether the original code is changed successfully.
```
new_code, succ = scts.change_file_style(["8.11", "0.1"], code)
```

You can also change the style of a directory which contains many code files with the same language, the parametres respectively represent target style list, original directory path, output directory path and output choice:
- -1: do not output
- 0: output only files changed successfully
- 1: output all files splited by succ and fail
- 2: output all files merged
```
scts.change_dir_style([style_choice], 'dataset/gcjpy_format', f'change/{style_choice}', output_choice=-1)
```

You can get the popularity of the single file's/directory's original styles by:
```
scts.get_file_popularity("5.1", code)
scts.get_dir_popularity("5.1", 'dataset/ProgramData/2')
```

**You can see the style's information** in {language}/transform\*.py's cvt_\* function's comments.

If you want to get AST's pdf, you can use:
```
scts.see_tree(code)
```
![捕获](https://github.com/rebibabo/SCTS/assets/80667434/70b5232b-75a9-4807-9b34-386de5cfe2ae)

If you want to get code's tokens, you can use:
```
scts.tokenize(code)
```
