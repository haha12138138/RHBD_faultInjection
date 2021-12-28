from typing import List
import re
def formatting(filepath:str,name:str) :
    with open(filepath+'/'+name,'r') as f:
        with open(filepath+'/'+name[:-2]+'_formatted.v','w+') as g:
            while True:
                start=f.readline()
                if start is not '':
                    start=start.strip()
                    tmp=start
                    while (';' not in tmp) and (tmp!='endmodule') and (tmp !=''):
                        tmp=f.readline().strip()
                        start+=tmp
                    if start != '':
                        g.write(start+'\n')
                else:
                    break
class wire:
    def __init__(self,name,fan=None,RH_level=0,slice=-1):
        if fan is None:
            self.fan=[]
        else:
            self.fan=[fan]
        self.value=False
        self.name=name
        self.RH_level=RH_level
        self.slice=slice
    def addfan(self,line_num):
        self.fan+=[line_num]
class cell:
    def __init__(self,name,lib_name,output_net:wire=None):
        self.name=name
        self.type=lib_name
        self.output=output_net
def get_hier_cell(root:dict,path:str) -> cell:
    a=a= path.split('/')[1:]if path[0]=='\\' else [path]
    tmp_ptr=root
    for level in a:
        tmp_ptr=tmp_ptr[level.strip()]
    return tmp_ptr
def print_hier_cell(root:dict,indent=0):
    for key,val in root.items():
        if isinstance(val,cell):
            # for _ in range(indent):
            #     print('\t',end='')
            # print(val.name.split('/')[-1])
            continue
        else:
            for _ in range(indent):
                print('\t',end='')
            print(key)
            print_hier_cell(val,indent+1)
            
def flatten_regional_cell(root:dict,path:str) -> List[cell]:

    def __flatten(root:dict)->List[cell]:
        celllist=[]
        for key,val in root.items():
            if isinstance(val,cell):
                celllist+=[val]
            else:
                celllist+=__flatten(root[key])
        return celllist

    def __traverse(root:dict,path:List[str]) -> List[cell]:
        if len(path) ==0:
            celllist=__flatten(root)
        else:
            key=path[0].strip()
            celllist=__traverse(root[key],path[1:])
        return celllist
        
    a= path.split('/')[1:]if path[0]=='\\' else [path]
    key=a[0].strip()
    ## for injecting into entire design. this function is not called
    return __traverse(root[key],a[1:])
    
def add_hier_cell(root:dict,path:str,leaf_cell:cell):
    a= path.split('/')[1:]if path[0]=='\\' else [path]
    def __add_hier_cell(root:dict,path:List[str],leaf_cell:cell):
        key=path[0].strip()
        if len(path) >= 2:
            if key not in root:
                root[key]=dict()
            __add_hier_cell(root[key],path[1:],leaf_cell)
        else:
            root[key]=leaf_cell
    key=a[0].strip()
    if len(a) ==1:
        root[key]=leaf_cell
    else:
        if key not in root:
            root[key]=dict()
        __add_hier_cell(root[key],a[1:],leaf_cell)

class netlist_result:
	def __init__(self,hier_dict,module_list,net_to_line_dict,watch_point_dict):
		self.hier_dict=hier_dict
		self.module_list=module_list
		self.net_to_line_dict=net_to_line_dict
		self.watch_point_dict=watch_point_dict
def netlist_to_graph(filepath:str,name:str):
    module_name_class_fmt=re.compile(r'([A-Z0-9_]+) ([\\/_a-zA-Z0-9 \[\]]+) \((.*)\).*')
    module_port_fmt=re.compile(r' *.([A-Z]+[A-Z0-9]*)\(([\\/_a-zA-Z0-9 \[\]]+)\)')
    slice_fmt=re.compile(r'(\S+) *\[([0-9]+)]')
    watch_point_name_fmt=re.compile(r'([^\[\] ]+)')
    line_counter=0
    module_line_start=False
    line_offset=0
    net_to_line_dict=dict()  # name:Wire() <- Contains fanout, RH_level, name
    cell_to_line_dict=dict() # name: offsetted_line_num
    # a tree.
    # naming is in format :\top/lv1/lv2/.../leaf
    # 1. parse name into chunks separated by '/'
    # 2. ignore the first and the last.
    # 3. if it is not in the layer create one
    # 4. leaf node is a cell
    hier_dict=dict()
    watch_point_dict=dict()
    module=[] # line_num: leaf module
    with open(filepath+'/'+name,'r') as f:
        tmp=f.readline()
        while tmp!='':
            if (tmp!='\n') and ('module' not in tmp[0:9]) and ('input' not in tmp[0:9]) and ('output' not in tmp[0:9]) \
               and ('wire' not in tmp[0:9]) and ('endmodule' not in tmp[0:9]):
                if(module_line_start==False):
                    module_line_start=True
                    line_offset=line_counter
                # this is the place that a module is read
                a=module_name_class_fmt.match(tmp.strip())
                lib=a.group(1)
                name=a.group(2)
                port_list=module_port_fmt.findall(a.group(3))
                # create a module and set its library name and cell name
                # record this line number to line dict indexing using input net name. if line exists in the dict append, else create a list
                # record this line number to line dict indexing using output net name.
                c=cell(name, lib)
                isRHcell='RH' in lib
                for port,net in port_list:
                    net=net.strip()
                    t=slice_fmt.search(net)
                    if t is None:
                        slice=-1
                        netname=net.strip()
                    else:
                        slice=int(t.group(2))
                        netname=t.group(1)
                    if (port == 'Y') or (port == 'Q'):
                        if net not in net_to_line_dict:
                            if slice is not None:
                                net_to_line_dict[net]=wire(netname,RH_level=int(isRHcell),slice=slice)
                            else:
                                net_to_line_dict[net]=wire(netname,RH_level=int(isRHcell))
                        else:
                            net_to_line_dict[net].name=netname
                            
                        if (port == 'Q'):
                            realname = watch_point_name_fmt.match(netname).group(1)
                            if realname not in watch_point_dict:
                                watch_point_dict[realname]=1
                            else:
                                watch_point_dict[realname]+=1
                        c.output=net_to_line_dict[net]
                        module+=[c]
                    else:
                        if net in net_to_line_dict:
                            net_to_line_dict[net].addfan(line_counter-line_offset)
                        else:
                            if slice is not None:
                                net_to_line_dict[net]=wire('',line_counter-line_offset,slice=slice)
                            else:
                                net_to_line_dict[net]=wire('',line_counter-line_offset)
                cell_to_line_dict[name]=line_counter-line_offset
                # add cell to hierarchical map
                add_hier_cell(hier_dict,c.name,c)
            tmp=f.readline()
            line_counter+=1
    return netlist_result(hier_dict, module,net_to_line_dict,watch_point_dict)



