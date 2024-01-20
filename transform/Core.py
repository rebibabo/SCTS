from ist_utils import text

class Core:
    def __init__(self, root, lang):
        self.root = root
        self.lang = lang
        self.code = text(root)
        self.match_nodes = []
        self.operations = []

    def match(self, u):
        if self.check(u): self.match_nodes.append(u)
        for v in u.children: self.match(v)

    def convert(self):
        # get operations
        for node in self.match_nodes:
            op = self.get_opts(node)
            if op: self.operations.extend(op)
        
        # insert and delete
        diff = 0
        ncode = self.code
        self.operations = sorted(self.operations, key=lambda x: (x[0], 1 if type(x[1]) is int else 0, -len(x[1]) if type(x[1]) is not int else 0))
        for op in self.operations:
            if type(op[1]) is int:  
                if op[1] < 0: del_num = op[1]
                else: del_num = op[1] - op[0]
                ncode = ncode[:op[0] + diff + del_num] + ncode[op[0] + diff:]
                diff += del_num
            else:                 
                ncode = ncode[:op[0] + diff] + op[1] + ncode[op[0] + diff:]
                diff += len(op[1])
        
        self.succ = ncode.replace(' ','').replace('\n', '') != self.code.replace(' ','').replace('\n', '')
        if self.succ:
            self.code = ncode
    
    def run(self):
        self.match(self.root)
        self.convert()
        return self.code, self.succ