import fileinput, re

def replace(match):
    word = (' ' if match.group(0).count(' ') > 0 else '') + '*' * match.group(0).count('*')
    return word

def normalize(declaration):
    # 去除 // 中文注释
    if '//' in declaration:
        declaration = declaration.split('//')[0]
        declaration += '' if declaration.endswith("\n") else '\n'
    pattern = r'(?<=\w)\s*(?<!\/)\**\s+' # 匹配不规范的定义
    declaration = re.sub(pattern, replace, declaration)
    return declaration

output_str = ""
depth = 0
collect = 0
origAliaseName = {}

for tmpline in fileinput.input():
    if len(tmpline.strip()) == 0:
        continue
    tmpline = normalize(tmpline)
    if ("struct" in tmpline or "union" in tmpline or "enum" in tmpline) and "{" in tmpline:

        if "typedef" in tmpline and depth == 0: # 最外层结构体有别名
            m0 = re.search(r' +(struct|union|enum) +(\w*) *{ *', tmpline) # 提取真名
            if m0 is not None and m0.group(2) == "": # typedef struct/union/enum后没有名字
                tmpline = re.sub(r'\b(struct|union|enum)\b', r'\1 PLAceHOLder', tmpline)
        tmpline = re.sub(r' *typedef +', '', tmpline) # 删除typedef，避免与重命名代码的typedef冲突

        collect = 1
        output_str += tmpline
        depth = depth + 1
    elif "{" in tmpline and collect == 1:
        output_str += tmpline
        depth = depth + 1
    elif "}" in tmpline and collect == 1:
        output_str += tmpline
        depth = depth - 1
        if depth == 0:
            m1 = re.search(r' *} *(\** *\w+) *;', tmpline) # 最外层结构体有别名，提取别名
            if m0 is not None:
                if m1 is not None:
                    if m0.group(2) == "": # typedef struct/union/enum后没有名字，使用别名
                        output_str = output_str.replace('PLAceHOLder', m1.group(1))
                        origAliaseName[m1.group(1)] = m1.group(1) # 真名：别名
                    else:
                        origAliaseName[m0.group(2)] = m1.group(1) # 真名：别名
                else:
                    output_str.replace('PLAceHOLder', "")
            collect = 0
            print(output_str)
            output_str = "" # 一个结构体结束，输出字符串置空
    elif "typedef" in tmpline and "{" not in tmpline and ";" in tmpline:
        print(tmpline) # 处理原有代码中的typedef origName aliaseName重命名;
    elif collect == 1:
        output_str += tmpline

for key, val in origAliaseName.items():
    m = re.search(r'(\**)( *)(\w+)', val)
    val = m.group(1) + m.group(3) # 移除val中的空格
    print(f"typedef {key} {val}; /* Automatically added by the program, error code */")