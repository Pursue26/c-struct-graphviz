import fileinput
import re

enum_member_default_type = "enum" # int

def convert_key(key):
    """
    将特殊值转换为指定值

    参数: 
    key: 特殊值

    返回: 
    转换后的键
    """
    key = re.sub(r'\*', "_", key)
    key = re.sub(r'\[', "_", key)
    key = re.sub(r'\]', "_", key)
    return key


def process_struct_or_union_or_enum(tmpline, depth, node_type):
    """
    处理结构体或联合体的定义

    参数: 
    tmpline: 当前行的代码字符串
    depth: 当前代码块的嵌套深度
    node_type: 当前代码块的类型（"struct", "union" or "enum"）
    nodeName: 当前代码块的名称

    返回: 
    depth: 更新后的嵌套深度
    node_type: 更新后的代码块类型
    nodeName: 更新后的代码块名称
    """
    depth += 1
    if "union" in tmpline:
        node_type = "union"
    elif "enum" in tmpline:
        node_type = "enum"
    m = re.search(r'\s*(struct|union|enum)\s*([0-9a-zA-Z_]*)\s*{\s*', tmpline)
    assert m is not None
    nodeName = m.group(2)
    return depth, node_type, nodeName


def process_closing_brace(tmpline, nodeName, stack, depth, strus):
    """
    处理闭合大括号

    参数: 
    tmpline: 当前行的代码字符串
    nodeName: 当前代码块的名称
    stack: 代码块的堆栈
    depth: 当前代码块的嵌套深度
    strus: 存储结构体和联合体的列表

    返回: 
    stack: 更新后的代码块堆栈
    depth: 更新后的嵌套深度
    """
    m = re.search(r'}\s*([0-9a-zA-Z_\-\[\]\*]*)\s*\;\s*', tmpline)
    assert m is not None
    struct_name = m.group(1)
    if struct_name == "":
        struct_name = nodeName
    top_node = stack[-1]
    curList = []
    curObj = {}
    while top_node["_depth"] == depth:
        curList.append(top_node)
        node_type = top_node["_node_type"]
        stack.pop()
        if len(stack) == 0:
            break
        top_node = stack[-1]
    curObj["val"] = curList
    curObj["key"] = struct_name
    curObj["convert_key"] = convert_key(struct_name)
    depth -= 1
    curObj["_depth"] = depth
    curObj["_node_type"] = node_type
    curObj["_cur_node_type"] = "stru"
    stack.append(curObj)
    if depth == 0:
        strus.append(stack[0])
        stack = []
    return stack, depth


def process_fieldobj(tmpline, depth, node_type, stack):
    """
    处理字段对象

    参数: 
    tmpline: 当前行的代码字符串
    depth: 当前代码块的嵌套深度
    node_type: 当前代码块的类型（"struct", "union" or "enum"）
    stack: 代码块的堆栈

    返回: 
    stack: 更新后的代码块堆栈
    """
    fieldobj = {}
    tmpline = re.sub(r'; *', '', tmpline)
    tmpline = tmpline.strip()
    if "(" in tmpline:
        m = re.search(r'.*\(\s*\*\s*([0-9a-zA-Z_\-]+)\).*', tmpline)
        fieldobj["val"] = tmpline
        assert m is not None
        fieldobj["key"] = m.group(1)
        fieldobj["convert_key"] = convert_key(fieldobj["key"])
        fieldobj["_depth"] = depth
        fieldobj["_cur_node_type"] = "func"
    else:
        tmpline = re.sub(r'struct', '', tmpline)
        tmpline = tmpline.strip()
        # 单行有逗号，也必须有分号才是true，否则可能是enum类型的成员，不能进入这个if
        if "," in tmpline and ";" in tmpline:
            fieldListOri = tmpline.split(",")
            fieldList = fieldListOri[0].split(" ")
            for field in fieldListOri[1:len(fieldListOri)]:
                fieldobj = {}
                fieldobj["val"] = " ".join(fieldList[0:-1])
                fieldobj["key"] = field.strip(" ")
                fieldobj["convert_key"] = convert_key(fieldobj["key"])
                fieldobj["_depth"] = depth
                fieldobj["_cur_node_type"] = "attr"
                fieldobj["_node_type"] = node_type
                stack.append(fieldobj)
            fieldobj = {}
            fieldobj["val"] = " ".join(fieldList[0:-1])
            fieldobj["_depth"] = depth
            fieldobj["_cur_node_type"] = "attr"
            fieldobj["_node_type"] = node_type
            fieldobj["key"] = fieldList[-1]
            fieldobj["convert_key"] = convert_key(fieldobj["key"])
            stack.append(fieldobj)
            return stack
        else:
            fieldList = tmpline.split(" ")
            name = fieldList[-1].strip()
            fieldobj["val"] = " ".join(fieldList[0:-1])
            fieldobj["key"] = name.replace(",", "") # 考虑有enum的成员进入该分支，移除末尾的分号
            fieldobj["convert_key"] = convert_key(fieldobj["key"])
            fieldobj["_depth"] = depth
            fieldobj["_cur_node_type"] = "attr"
    fieldobj["_node_type"] = node_type
    # 处理 enum 成员的类型，设置为默认类型
    if fieldobj["_node_type"] == "enum" and fieldobj["val"] == "":
        fieldobj["val"] = enum_member_default_type
    stack.append(fieldobj)
    return stack


def process_code(fileinput):
    """
    处理输入代码的函数

    参数: 
    fileinput: 输入的代码文件

    返回: 
    strus: 结构体或联合体的列表
    """
    depth = 0
    strus = []
    stack = []
    node_type = "struct"
    nodeNames = []
    aliases = {} # 存储结构体别名映射关系的字典

    for tmpline in fileinput:
        if ("struct" in tmpline or "union" in tmpline or "enum" in tmpline) and "{" in tmpline:
            depth, node_type, nodeName = process_struct_or_union_or_enum(tmpline, depth, node_type)
            nodeNames.append(nodeName)
        elif "}" in tmpline:
            nodeName = nodeNames.pop()
            stack, depth = process_closing_brace(tmpline, nodeName, stack, depth, strus)
        elif "typedef" in tmpline:
            # 处理结构体重命名的情况，如typedef DL_HEAD_S HASH_LIST_S; typedef struct thpool_ thpool_;
            m = re.search(r' *typedef +(\w+|struct +\w+) +(\**\w+) *;', tmpline)
            if m is not None:
                aliases[m.group(2)] = m.group(1) # key为别名，val为原名
        else:
            stack = process_fieldobj(tmpline, depth, node_type, stack)

    return strus, aliases


def generate_dot_text(strus, aliases):
    dotText = '''
digraph {
    graph [pad="0.5", nodesep="0.5", ranksep="2", dpi=300];
    node [shape=plain]
    rankdir=LR;
'''
    linkStr = ""
    nodeStack = []
    sset = {"mock"} # struct name (key) set
    for s in strus:
        s["path"] = s["convert_key"]
        nodeStack.append(s)
        sset.add(s["key"])
    while len(nodeStack) > 0:
        curNode = nodeStack.pop()
        key = curNode["key"]
        dotText += """    {} [label=<
        <table border="0" cellborder="1" cellspacing="0">
        <tr><td colspan="2" port="head"><i>{}</i></td></tr>\n""".format(curNode["path"], key)
        vals = curNode["val"][::-1] # 反转是为了按结构体成员顺序输出
        for row in vals:
            replacedKey = row["convert_key"]
            if isinstance(row["val"], list):
                tmpNode = {}
                tmpNode["key"] = row["key"]
                tmpNode["convert_key"] = row["convert_key"]
                tmpNode["val"] = row["val"]
                tmpNode["path"] = row["convert_key"]
                nodeStack.append(tmpNode)
                tmpLinkStr = "    {}:{}->{}:head\n".format(curNode["path"], tmpNode["path"], row["key"])
                linkStr += tmpLinkStr
                sset.add(tmpNode["path"])
            nodeType = row["val"]
            if isinstance(row["val"], list):
                nodeType = row["_node_type"]
            if not isinstance(row["val"], list):
                linkFlag = False
                if row["val"] in sset and linkFlag == False:
                    tmpLinkStr = "    {}:{}->{}:head [style=\"{}\"]\n".format(curNode["path"], replacedKey, row["val"], 
                    "solid" if curNode["path"] != row["val"] else "invis")
                    linkStr += tmpLinkStr
                elif row["val"] in aliases and linkFlag == False: # 处理成员为结构体别名的情况，若别名在别名字典中
                    origName = aliases[row["val"]] # 真名
                    if origName in aliases: # 原名还是别名
                        origName = aliases[origName]
                    if origName in sset: # 真名在入参 strus 里面
                        # 重命名结构指向真名结构时使用虚线
                        tmpLinkStr = "    {}:{}->{}:head [style=\"dashed\"]\n".format(curNode["path"], replacedKey, origName)
                        linkStr += tmpLinkStr
            if row["_cur_node_type"] == "func":
                dotText += """    <tr><td colspan="2" port="{}">{}</td></tr>\n""".format(replacedKey, row["val"])
            else:
                dotText += """    <tr><td>{}</td><td port="{}">{}</td></tr>\n""".format(nodeType, replacedKey, row["key"])
        dotText += """    </table>>];\n"""
    dotText += linkStr
    dotText += """}"""
    return dotText


def main():
    strus, aliases = process_code(fileinput.input())
    # print(strus)
    # print(aliases)
    dotText = generate_dot_text(strus, aliases)
    print(dotText)


if __name__ == "__main__":
    main()
