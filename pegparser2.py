stk=[]

def stackshow(fn):
    def func(*args):
        global stk
        stk.append(args[0].ver)

##        file = args[1].file
##        ptr=args[1].ptr
##        cfile = file[:ptr]+'^'+file[ptr:]
##        print(cfile)
        
        print('.'.join(stk)+'>')
        
        ret = fn(*args)
        stk=stk[:-1]
        print('.'.join(stk)+'<'+'-+'[ret.succ])

##        file = ret.file
##        ptr = ret.ptr
##        cfile = file[:ptr]+'^'+file[ptr:]
##        print(cfile)
        
        return ret
    
    return func
    
def copyout(fn):
    def fn2(*args):
        ret = fn(*args)
        return ret.copy()
    return fn2

class process_node:
    def __init__(self,ver,data=None, chldrn=None):
        self.ver = ver
        self.data=data
        self.children = [] if chldrn==None else chldrn
    def start(self, file):
        iState = state(True, 0, file, [capture(0,name="Root")], True)
        rState = self.run(iState)
        return rState

##    @stackshow
    @copyout
    def run(self, pState):
        cState = pState.copy()
        rFile=cState.file[cState.ptr:]
        ver=self.ver
        if ver == "TERMINATE":
            cState.succ=True
            return cState
        if ver == "str":
            if len(rFile) >= len(self.data) and rFile.startswith(self.data):
                cState.ptr+=len(self.data)
                cState.succ=True

                nState = self.children[0].run(cState)
                return nState
            else:
                cState.succ = False
                return cState
        if ver == "star":
            while cState.succ:
                cState = self.children[0].run(cState)
            nState = self.children[1].run(cState)
            return nState
        if ver == "oneormore":
            cState.succ = self.children[0].run(cState).succ
            if not cState.succ:
                return cState
            while cState.succ:
                cState = self.children[0].run(cState)
            nState = self.children[1].run(cState)
            return nState
        if ver == "alt":
            for child in self.children:
                nState = child.run(cState)
                if nState.succ:
                    return nState
            else:
                cState.succ=False
                return cState
##        if ver == "call":
##            cState = self.children[0].run(cState)
##            if cState.succ:
##                cState = self.children[1].run(cState)
##            return cState
        if ver == "call":
            for child in self.children:
                cState=child.run(cState)
                if not cState.succ:
                    return cState
            return cState
        
        if ver == "test":
            cState.canCap=False
            cState.succ = self.children[0].run(cState).succ
            cState.canCap=True
            return cState
        
        if ver == "ntest":
            cState.canCap=False
            cState.succ = not self.children[0].run(cState).succ
            cState.canCap=True
            return cState

        if ver == "opt":
            fState=self.children[0].run(cState)
            if fState.succ:
                cState=fState
            cState = self.children[1].run(cState)
            return cState

        if ver == "range":
            if len(rFile)>0 and ord(self.data[0]) <= ord(rFile[0]) <= ord(self.data[1]):
                cState.ptr+=1
                cState.succ=True
                nState = self.children[0].run(cState)
                return nState
            else:
                cState.succ=False
                return cState

        if ver == "cap":
            if cState.canCap:
                name = self.data
                ncap = capture(start=cState.ptr, name=name)
                cState.caps[-1].children.append(ncap)
                cState.caps.append(ncap)

            nState = self.children[0].run(cState)

            if cState.canCap:
                if nState.succ:
                    for x in cState.caps:
                        x.end=nState.ptr-1
                    cState.caps.pop(-1)
    ##                return nState
                else:
                    cState.caps.pop(-1)
                    cState.caps[-1].children.pop(-1)
            
            return nState
        


class state:
    def __init__(self, succ, ptr, file, caps, canCap):
        self.succ=succ
        self.ptr=ptr
        self.file=file
        self.caps=caps
        self.canCap=canCap
    def copy(self):
        return state(self.succ,self.ptr,self.file,self.caps,self.canCap)
    def __repr__(self):
        return f"Success?: {self.succ}\nCap: {self.file[:self.ptr]!r}\nElse: {self.file[self.ptr:]!r}\n{self.caps[0]!r}\n"

class capture:
    def __init__(self,start, end=None, name=None):
        self.start=start
        self.end=end
        self.name=name
        self.children=[]

    def __repr__(self):
        return self.pretty_repr(0)[:-1]

    def pretty_repr(self,ind):
        o=''
        name = '!' if self.name == '' else self.name
        o+=('    '*ind+f'<{name} {self.start}-{self.end}>')+'\n'
        for child in self.children:
            o+=child.pretty_repr(ind+1)
        return o

##tree = (obj1:=process_node('alt'))
##obj1.children.append(obj2:=process_node('str','hello '))
##obj2.children.append(obj2:=process_node('TERMINATE'))
##obj1.children.append(obj2:=process_node('str','world'))
##obj2.children.append(obj2:=process_node('TERMINATE'))

##tree = (opt:=process_node('opt'))
##opt.children.append(obj:=process_node('cap','hi'))
##obj.children.append(obj:=process_node('str','hello '))
##obj.children.append(obj:=process_node('TERMINATE'))
##opt.children.append(obj:=process_node('str','world'))
##obj.children.append(obj:=process_node('TERMINATE'))

##tree = (S:=process_node('alt'))
##S.children.append(obj1:=process_node('str','a'))
##obj1.children.append(call:=process_node('call'))
##call.children.append(obj1:=S)
##call.children.append(obj1:=process_node('str','a'))
##obj1.children.append(obj1:=process_node('TERMINATE'))
##
##S.children.append(obj2:=process_node('str','a'))
##obj2.children.append(obj2:=process_node('TERMINATE'))

alts = 'weakalts'

####
TERM = process_node('TERMINATE')

####
ident = \
process_node('cap', 'Ident',chldrn=[
    process_node('oneormore',chldrn=[
        process_node('alt',chldrn=[
            process_node('range',('a','z'),chldrn=[TERM]),
            process_node('range',('A','Z'),chldrn=[TERM]),
            process_node('range',('0','9'),chldrn=[TERM]),
        ]),
        TERM,
    ])
])

####
skip = \
process_node('star',chldrn=[
    process_node('str',' ',chldrn=[TERM]),
    TERM,
])

####
alt = \
process_node('cap', 'Alt',chldrn=[
    process_node('alt',chldrn=[
        process_node('call',chldrn=[
            ident,
            process_node('star',chldrn=[
                process_node('call',chldrn=[
                    skip,
                    ident,
                ]),
                TERM,
            ]),
        ]),
        process_node('call',chldrn=[
            process_node('str','(',chldrn=[TERM]),
            skip,
            alts,
            skip,
            process_node('str',')',chldrn=[TERM]),
        ]),
    ]),
])

####
alts = \
process_node('cap', 'Alts',chldrn=[
    process_node('call',chldrn=[
        alt,
        skip,
        process_node('star',chldrn=[
            process_node('call',chldrn=[
                process_node('str','/',chldrn=[TERM]),
                skip,
                alt,
                skip,
            ]),
            TERM,
        ]),
    ]),
])

####
rule = \
process_node('call',chldrn=[
    ident,
    skip,
    process_node('str','<-',chldrn=[TERM]),
    skip,
    alts,
])


def recu_fix(node):
    for i,child in enumerate(node.children):
        if child == "weakalts":
            node.children[i]=alts
        else:
            recu_fix(child)

recu_fix(rule)

##print(alt.start('expr1 / expr2'))
print(rule.start('rule <- expr1 / expr21 expr22 / (exp)'))
