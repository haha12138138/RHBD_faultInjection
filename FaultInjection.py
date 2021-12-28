'''
input:
1. design : dut from cocotb
2. netlist_path, netlist_name
function:
    read netlist
        receive:
        formatted netlist
    \/
    get all module's output and hierarchy.
    through parsing netlist netlist_to_graph.py
        receive:
        hier_dict and module list
    \/
    select area to inject fault:
    1. specific point via hier_dict
    2. specific level of hierachy via hier_dict
        will need to flatten certain levels
    3. entire design via module list
    and get names of all the output nets
    \/
    get handles for simobjects using name via cocotb
    HierarchyObject._id(name)
    \/
    generate 100 input
    for all signals:
        choose 1 signal to force 0 for 1 clock cycle
        apply 100 input, record the result
        choose the same signal and force 1 for a clock cycle
        apply 100 input, record the result
        choose the same signal and release it
        apply 100 input ,record the result
        compare calculate error rate. set frequency for normal lib as 1 RH lib as 0.1
'''
from typing import List
import cocotb
import netlist_to_graph as parser
import os
from enum import Enum
import random
#os.stat('./'+netlist_name).st_mtime > os.stat('./'+formatted_name).st_mtime
class FaultInjectStrategy(Enum):
    Global=0
    Regional=1
    Local=2

class InputVectorStrategy(Enum):
    Random = 0
    FromFile = 1

class handler_info:
    def __init__(self, handle, width):
        self.handle = handle
        self.width = width

class EdgeType(Enum):
	Falling=0
	Rising=1
	NoEdge=3
class FaultLogEntry:
	def __init__(self,watch_point_width):
		self.number_of_faults=0
		self.BitVector=[0 for _ in range(watch_point_width)]

	def update(self,diff):
		idx=0
		if diff!=0:
			self.number_of_faults+=1
		while diff != 0:
			self. BitVector[idx]+=diff&1
			diff >>=1
			idx+=1
	def getDistribution(self):
		return self.BitVector

class FaultLog:
	def __init__(self,tracelength,watch_point_width):
		# (number of faults, distribution)
		self.log=dict()
		self.tracelength=tracelength
		self.distribution_width=watch_point_width

	def createEntry(self,name,init_val):
		self.log[name]=init_val

	def __updateEntry(self,name,val):
		
		self.log[name].update(val)
	
	def printLog(self):
		for k,v in self.log.items():
			print('key: '+k+' ,fault_rate: '+str(v.number_of_faults/self.tracelength))

	def getDistribution(self,name=None):
		if name ==None:
			t=[0 for _ in range(self.distribution_width)]
			for k,entry in self.log.items():
				t= list(map(lambda x,y: x+y,t,entry.getDistribution()))
		else:
			t=self.log[name].getDistribution()
		return t

	async def logResult(self,driver,EntryName):
		tmp=[0,0]
		idx=0
		async for value in driver:
			print('t='+str(idx)+' val= '+str(hex(value)))
			tmp[idx]=value
			idx+=1

		if not (tmp[0]== tmp[1]) :
			self.__updateEntry(EntryName,tmp[0]^tmp[1])
			print('Not Equal')
		else:
			print('Equal')
			

class FaultInjection:
	def __init__(self, netlist_path: str, netlist_name: str, dut,numofInjectedSig):
		formatted_name = netlist_name[:-2] + '_formatted.v'
		parser.formatting(netlist_path, netlist_name)
		result= parser.netlist_to_graph(netlist_path, formatted_name)
		self.hier_dict=result.hier_dict
		self.module_list=result.module_list
		self.net_to_line_dict=result.net_to_line_dict
		self.watch_point_dict=result.watch_point_dict
		self.check_point = ''
		self.dut = dut
		self.Injectstrategy: FaultInjectStrategy = FaultInjectStrategy.Regional
		self.DriverStrategy: InputVectorStrategy = InputVectorStrategy.Random
		self.path : str=''
		self.InjectDriver=None
		self.log=None
		self.numofInjectedSig=numofInjectedSig
	def configLog(self,tracelength,check_point_width):
		self.log=FaultLog(tracelength,check_point_width)

	def print_hierarchy(self):
		parser.print_hier_cell(self.hier_dict)

	def print_check_point(self):
		for k in self.watch_point_dict:
			print(k)

	def get_check_point(self,name):
		result=self.get_signal_handler(user_selected=[name],width=self.watch_point_dict[name])[0]
		return result

	def select_strategy(self, inj_strategy: FaultInjectStrategy, drv_strategy: InputVectorStrategy,path:str):
		self.Injectstrategy = inj_strategy
		self.DriverStrategy = drv_strategy
		self.path=path

	def get_signal_handler(self,user_selected=None,width=0) -> List[handler_info]:
		ret : List[handler_info] = []
		if user_selected is None:
			if self.Injectstrategy == FaultInjectStrategy.Global:
				scope = self.module_list
			elif self.Injectstrategy == FaultInjectStrategy.Regional:
				scope = parser.flatten_regional_cell(self.hier_dict, self.path)
			else:
				scope = [parser.get_hier_cell(self.hier_dict, self.path)]
			for mod in scope:
				name = mod.output.name.strip('\\')
				topname = 'U1' + '.'
				ret += [handler_info(self.dut._id(topname + name, False), mod.output.slice)]
		else:
			for mod in user_selected:
				name = mod.strip('\\')
				topname = 'U1' + '.'
				ret += [handler_info(self.dut._id(topname + name, False), width)]
		return ret

	def select_signal(self, handle_infos: List[handler_info]):
		for _ in range(10):
			a = random.choice(handle_infos)
			if a.width == -1:
				return a.handle
		raise "Cannot select"
