
def get_problems(example,input_difficultys):
    template = '''
# {problem_name} Problem Description:
{description}

# Problem to Solve: 
{problem_detail}

# Instruction:
Please reasoning step by step and output your final answer in \\boxed{{}}.
'''
    contents = []
    for input_difficulty in input_difficultys:
        content = template.format(problen_name = example[''])