from exec_and_verify import *
# 用一个简单的测试例子来验证
code = """
def generator():
    import random  # 确保在函数内部导入random
    n = random.randint(1, 999)
    max_edges = n * (n - 1) // 2
    m = random.randint(0, min(999, max_edges))
    
    seen_edges = set()
    edges = []
    while len(edges) < m:
        u = random.randint(1, n)
        v = random.randint(1, n)
        if u == v:
            continue
        edge_canon = (min(u, v), max(u, v))
        if edge_canon not in seen_edges:
            seen_edges.add(edge_canon)
            edges.append((u, v))
    
    res = f"{n} {m}"
    for u, v in edges:
        res += f"\n{u} {v}"
    return res
"""

code =  fix_newlines_in_python_strings(import_needed_module_for_python(code)) 


# print(repr(code))  # 使用 repr() 来显示所有特殊字符

        
# 确保代码可以执行
try:
    exec(code)
    test_case_input = generator()
    print(test_case_input)  # 打印生成的测试用例
except Exception as e:
    print(f"Error in exec generator ! {e}")
