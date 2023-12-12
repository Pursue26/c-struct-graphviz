import fileinput, re

def replace(match):
    word = match.group(0)
    new_word = ' ' + word[::-1].strip()
    return new_word

def normalize(declaration):
    # 匹配不规范的定义
    pattern = r'((?<!\/)\*+\s+)'
    declaration = re.sub(pattern, replace, declaration)
    pattern = r'(?<=\w)\s{2,}'
    declaration = re.sub(pattern, ' ', declaration)

    return declaration

output_str = ""
depth = 0
collect = 0

for tmpline in fileinput.input():
    tmpline = normalize(tmpline)
    if "struct" in tmpline and "{" in tmpline:
        collect = 1
        output_str = tmpline
        depth = depth + 1
    elif "{" in tmpline and collect == 1:
        output_str += tmpline
        depth = depth + 1
    elif "}" in tmpline and collect == 1:
        output_str += tmpline
        depth = depth - 1
        if depth == 0:
            collect = 0
            print(output_str)
    elif collect == 1:
        output_str += tmpline