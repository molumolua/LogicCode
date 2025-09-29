import math
testcases = int(input())
for x in range(testcases):
    const = int(input())
    n = 360/(180-const)
    if n == math.floor(n):
        print("YES")
    else: print("NO")