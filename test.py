# # 

# generate_test_case_prompt = '''
# You are given a problem statement from an algorithmic competition. Your task is to generate a list of valid test cases for this problem, in the format of a JSON array. Each element in the array should be an object with a key 'test_case' and the corresponding value should be a string representing a valid input for the problem. The input should follow the problem description, and for problems that involve multiple test cases, each input should be a single test case represented as a string. 

# ### Specific requirements:
# 1. Each test case should contain a single, valid input that adheres to the problem statement.
# 2. If the problem involves multiple test cases, the input should include the count of test cases (1) as the first line.
# 3. The number of tokens in each test case should not exceed 200 tokens.
# 4. The test cases in the list should be ordered from simplest to most complex.
  
# ### Example format for the output (JSON array):
# ```json
# [
#   {{
#     "test_case": "input1"
#   }},
#   {{
#     "test_case": "input2"
#   }},
#   ...
# ]
# ```
# The input problem statement may include various types of data, such as integers, strings, arrays, etc., and you should ensure the test cases conform to these formats.

# **Problem Statement:**
# {problem}
# '''

# print(generate_test_case_prompt.format(problem="123"))

import re

def is_valid_number(s: str) -> bool:
    # 使用正则表达式检查是否是有效的整数或浮点数
    return bool(re.fullmatch(r'^\s*-?\d+(\.\d+)?\s*$', s.strip()))


print(is_valid_number("1"))        # True
print(is_valid_number("2 3"))      # False
print(is_valid_number("23"))       # True
print(is_valid_number("2\n3"))     # False
print(is_valid_number("2\n"))      # True
print(is_valid_number("1 1.23"))     # False
print(is_valid_number(" 2\n"))       # True
print(is_valid_number("1."))       # False
print(is_valid_number("1.23 "))    # True
print(is_valid_number(" 01.23"))    # False
print(is_valid_number("-0.23"))     # True
