import math, re, sys, string, operator, functools, fractions, collections
sys.setrecursionlimit(10**7)
RI=lambda x=' ': list(map(int,input().split(x)))
RS=lambda x=' ': input().rstrip().split(x)
dX= [-1, 1, 0, 0,-1, 1,-1, 1]
dY= [ 0, 0,-1, 1, 1,-1,-1, 1]
mod=int(1e9+7)
eps=1e-6
pi=math.acos(-1.0)
MAX=10**5+10
#################################################
n=RI()[0]
def check(n):
    cnt=[0,0]
    while n:
        if n%10==4:
            cnt[0]+=1
        else:
            cnt[1]+=1
        n//=10
    return (cnt[0]==cnt[1])
for l in range(2,11,2):
    for i in range(1<<l):
        num=i
        v=0
        for j in range(l-1,-1,-1):
            v*=10
            if (num>>j)&1:
                v+=7
            else:
                v+=4
        if v>=n and check(v):
            print(v)
            exit(0)
        
    
