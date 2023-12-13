import fileinput, re

def replace(match):
    word = (' ' if match.group(0).count(' ') > 0 else '') + '*' * match.group(0).count('*')
    return word

def normalize(declaration):
    pattern = r'(?<=\w)\s*(?<!\/)\**\s+' # 匹配不规范的定义
    declaration = re.sub(pattern, replace, declaration)
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