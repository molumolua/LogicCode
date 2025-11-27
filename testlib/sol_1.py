t=int(input())
while(t):
    n=int(input())
    a=list(map(int, input().split(" ")))
    b=[]
    c={}
    for i in a:
        if(c.get(i,-1)==-1):
            c[i]=1
            b.append(i)
    for i in b:
        print(i,end=" ")
    print("")
    t-=1