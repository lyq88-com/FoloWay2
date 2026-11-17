import sys
sys.path.insert(0,'.')
import app.main as m
a=m.app
uniq=set(); total=0; per=[]
for r in a.routes:
    if type(r).__name__=='_IncludedRouter':
        pre=getattr(r.include_context,'prefix','') or ''
        sub=r.original_router.routes
        n=0
        for rr in sub:
            if hasattr(rr,'methods'):
                total+=1; n+=1
                uniq.add((pre+rr.path, tuple(sorted(rr.methods))))
        per.append((pre,n))
    elif hasattr(r,'methods'):
        total+=1; uniq.add((r.path,tuple(sorted(r.methods))))
print('挂载的路由器:',len(per))
print('路由总数(含重复方法):',total)
print('唯一 path+method:',len(uniq))
print('唯一 path:',len(set(p for p,_ in uniq)))
print('GET/POST/PUT/DELETE 分布:')
from collections import Counter
c=Counter(meth for _,ms in uniq for meth in ms)
print(dict(c))
