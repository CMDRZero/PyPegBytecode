class stack:
    def __init__(self):
        self.data = []

    def __repr__(self):
        prev=10
        if len(self.data)<=prev:
            return f"stack(n={len(self.data)}, {self.data})"
        else:
            ist = str(self.data[:prev-1] + ['...'] + [self.data[-1]]).replace('\'...\'','...')
            return f"stack(n={len(self.data)}, {ist})"
    def debug(self):
        
        print( ' '.join([self.formatitem(x) for x in self.data]) )
    def formatitem(self,item):
        if len(item)>1:
            raise RuntimeError(f'Item {item} is wider than 1 character')
        if repr(item)[:3]=="'\\x":
            return '#'+str(ord(item))
        else:
            return item
    def pop(self):
        return self.data.pop(0)
    def popmany(self, n=1):
        vals = self.data[:n]
        self.data = self.data[n:]
        return vals
    def popParen(self):
        out = []
        ind = 0
        if self.data[0] != '(':
            raise RuntimeError(f'Unable to pop \'(\' from stack: {self!r}')
        else:
            out.append(self.pop())
            ind+=1
        while ind != 0:
            it = self.data.pop(0)
            ind += ({'(':+1,')':-1}).get(it,0)
            out.append(it)
        return out
    def push(self,item):
        self.data = [item] + self.data
    def pushmany(self,items):
        self.data = items + self.data

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

def parse_string(stck):
    mode = stck.pop()
    if mode == '!':
        return ''
    elif mode == '"':
        amt = parse_int(stck)
        return ''.join(stck.popmany(amt))
    elif mode == "'":
        return ''.join(stck.popmany(1))
    else:
        raise RuntimeError(f"Unknown string mode {mode}")

def parse_int(stck):
    amt = ord(stck.pop())+1
    ist = stck.popmany(amt)
    val = 0
    while ist != []:
        val *= 256
        val += ord(ist.pop(0))
    return val

def parse_instr(data):
    pass

instr_stack = stack()
data_stack = stack()
ptr_stack = stack()
root = capture(0,name="Root")
cap_stack = [root]
store={}

#instr_stack.data = list('<"\x00\x04Main<!\'h>"\x00\x04ello><!\' >')               #Old Test
#instr_stack.data = list('<"\x00\x04Main<!\'h/(\'H)>&("\x00\x04ello)>&(<!\' >)')   #Better Hello World Test
#instr_stack.data = list(':"\x00\x04test(<!\'!>)~"\x00\x04test')                   #Store restore test
#instr_stack.data = list(':\'x(<!\'a&(~\'x)/(\'b)>)~\'x')                          #Kleene star via store restore
#instr_stack.data = list('<!\x01*(\'a)>')                                          #Kleene star
#instr_stack.data = list('<!+(\'a)>')                                              #One or more
#instr_stack.data = list('<!\'a&(\'b?&(\'c))>')                                    #Optional test
#instr_stack.data = list('<!\x01*(.)>')                                            #Capture all
#instr_stack.data = list('<!\x01$>')                                               #False
#instr_stack.data = list('<!"\x00\x05hello&(@"\x00\x06 world^)>')                  #'hello' followed by ' world'
#instr_stack.data = list('<!"\x00\x05hello&(@"\x00\x06 world^$)>')                 #'hello' not followed by ' world'
#instr_stack.data = list('<!"\x00\x02hi&(@.^$)>')                                  #just 'hi' followed by EOF
#instr_stack.data = list('<!-az/(-AZ)>')                                           #range test
#instr_stack.data = list('<!@-az^$&(.)>')                                          #not in range test
instr_stack.data = list('<!:\'S(@\'a&(~\'S&(\'a&(\x01`)))/(^\'a))~\'S&(@.^$)>')                                          #Odd length

file = 'aaaa'


ptr = 0
#error
while True:
    print(file[:ptr]+'^'+file[ptr:],end=' :: ')
    print(ptr_stack,end=" :: ")
    (instr_stack.debug())
    if instr_stack.data==[]:
        break

    
    nex = instr_stack.pop()

    #Begin capture
    if nex == '<':
        name = parse_string(instr_stack)
        ncap = capture(start=ptr, name=name)
        cap_stack[-1].children.append(ncap)
        cap_stack.append(ncap)

    #End Capture
    elif nex == '>':
        #Success
        if data_stack.data[0]=='\x01':
            for x in cap_stack:
                x.end=ptr-1
            cap_stack.pop(-1)
        #Failure
        else:
            cap_stack.pop(-1)
            cap_stack[-1].children.pop(-1)

    #String Comparisons
    elif nex in ["'", '"', '!']:
        instr_stack.push(nex)
        match = parse_string(instr_stack)
        if len(file[ptr:])<len(match):
            data_stack.push('\x00')
        elif file[ptr:ptr+len(match)]==match:
            ptr+=len(match)
            data_stack.push('\x01')
        else:
            data_stack.push('\x00')

    #String Range Comparisons
    elif nex == '-':
        low = instr_stack.pop()
        high = instr_stack.pop()
        success = ptr<len(file) and ord(low) <= ord(file[ptr]) <= ord(high)
        ptr+=success
        data_stack.push(chr(success))
    
    #Unpacking parenthesis
    elif nex in ['(', ')']:
        pass
    
    #Pushing booleans
    elif nex in ['\x01', '\x00']:
        data_stack.push(nex)

    #Successive Checks
    elif nex == '&':
        topofdata=data_stack.pop()
        if topofdata=='\x01':
            pass
        else:
            data_stack.push(topofdata)
            instr_stack.popParen()
    
    #Fallbacks
    elif nex == '/':
        topofdata=data_stack.pop()
        if topofdata=='\x01':
            data_stack.push(topofdata)
            instr_stack.popParen()
        else:
            pass
    
    #Function Store
    elif nex == ':':
        ident = parse_string(instr_stack) 
        store[ident]=instr_stack.popParen()

    #Function Restore
    elif nex == '~':
        ident = parse_string(instr_stack) 
        instr_stack.pushmany(store[ident])

    #Kleene star
    elif nex == '*':
        topofdata=data_stack.pop()
        payload = instr_stack.popParen()
        if topofdata=='\x01':
            instr_stack.pushmany(payload + ['*'] + payload)
        else:
            data_stack.push('\x01')

    #One or more
    elif nex == '+':
        payload = instr_stack.popParen()
        instr_stack.pushmany(payload + ['&','(','\x01','*'] + payload + [')'])

    #Optionals always succeed
    elif nex == '?':
        data_stack.data[0]='\x01'

    #Anycapture
    elif nex == '.':
        if ptr < len(file):
            ptr+=1
            data_stack.push('\x01')
        else:
            data_stack.push('\x00')
    
    #Invert operand
    elif nex == '$':
        data_stack.data[0] = chr(1-ord(data_stack.data[0]))

    #Set Jumppoint
    elif nex == '@':
        ptr_stack.push(ptr)

    #Jump to Jumppoint
    elif nex == '^':
        ptr=ptr_stack.pop()

    #Pop jumppoint
    elif nex == '`':
        ptr_stack.pop()

    

    else:
        raise RuntimeError(f'Unknown instruction: {instr_stack.formatitem(nex)}')

if data_stack.data==['\x00']:
    print('Failure')
elif data_stack.data==['\x01']:
    print('Success')
else:
    print('Invalid Return Code')
