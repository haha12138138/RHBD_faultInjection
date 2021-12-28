import random
import cocotb
import matplotlib.pyplot as plt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge,ClockCycles,Timer,RisingEdge
from cocotb.handle import Force, Release, NonHierarchyIndexableObject
from FaultInjection import FaultInjection, FaultInjectStrategy, InputVectorStrategy, EdgeType,FaultLog,FaultLogEntry
import netlist_to_graph as parser
#@cocotb.test()
#async def test_dff_simple(dut):
#    """ Test that d propagates to q """
#    a_vector=[1,0,1,1,0,1,0,0]
#    b_vector=[0,1,0,1,0,0,1,0]
#    clock = Clock(dut.clk, 10, units="us")  # Create a 10us period clock on port clk
#    dut.rst.setimmediatevalue(1)
#    dut.a.setimmediatevalue(0)
#    dut.b.setimmediatevalue(0)
#    cocotb.start_soon(clock.start())  # Start the clock
#    await FallingEdge(dut.clk)
#    dut.rst.setimmediatevalue(0)
#    for i in range(4):
#        dut.a.value = a_vector[i]
#        dut.b.value = b_vector[i]
#        await FallingEdge(dut.clk)
#    for i in range(5):
#        if i<=2:
#            dut.inv_a1.value = Force(1)
#        elif i==3 :
#            dut.inv_a1.value = Release()
#        dut.a.value = a_vector[i]
#        dut.b.value = b_vector[i]
#        await FallingEdge(dut.clk)

async def initialize(dut):
	dut.EN.setimmediatevalue(0)
	dut.RSTn.setimmediatevalue(0)
	dut.KDrdy.setimmediatevalue(0)
	dut.Kin.setimmediatevalue(0)
	dut.Din.setimmediatevalue(0)
	await FallingEdge(dut.CLK)
	
async def enableOp(dut,enable=True):
	dut.EN.setimmediatevalue(1) 
	dut.RSTn.setimmediatevalue(1)
	await FallingEdge(dut.CLK)
	
async def sendKeyandData(dut,Kin:int,Din:int):
	dut.Kin.setimmediatevalue(Kin) 
	dut.Din.setimmediatevalue(Din) 
	dut.KDrdy.setimmediatevalue(1)
	await FallingEdge(dut.CLK)
	dut.KDrdy.setimmediatevalue(0) 
	
async def injectFault(handle,upsettime,unit='ns',delaytime=0,edge=0):
	if edge != 2 :
		await Timer(delaytime,units=unit)
		handle.value=Force(edge)
		await Timer(upsettime,units=unit)
		handle.value=Release()
	else:
		await Timer(2*delaytime,units=unit)

@cocotb.test()
async def simple_run(dut):
	async def Driver(Kin,Din,watch_point):
		dly=random.randint(15,100)
		for i in range(2):
			await initialize(dut)
			await enableOp(dut)
			await sendKeyandData(dut,Kin,Din)
			display.setimmediatevalue(i)	
			await cocotb.start(injectFault(a,10,'ns',delaytime=dly,edge=random.randint(0,1)))
			await FallingEdge(dut.BSY)
			await ClockCycles(dut.CLK,3,False)
			yield watch_point.value
	
	inj=FaultInjection(r'./','Syn_Custom_AES.v',dut,10)
	inj.select_strategy(FaultInjectStrategy.Regional,InputVectorStrategy.Random,path='\\U1/aes_core/SB0')
	handle_infos=inj.get_signal_handler()
	display=dut._id('string_sel',False)
	clock =Clock(dut.CLK,10, units='ns')
	cocotb.start_soon(clock.start())
	inj.print_check_point()
	watch_point_handleinfo=inj.get_check_point('Dout')
	inj.configLog(10,watch_point_handleinfo.width)
	log=inj.log
	
	#select 10 signals
	for _ in range(inj.numofInjectedSig):
		a=inj.select_signal(handle_infos)
		print(a._name)
		log.createEntry(a._name,FaultLogEntry(watch_point_handleinfo.width))
		Din=0x00112233445566778899AABBCCDDEEFF
		Kin=0x000102030405060708090A0B0C0D0E0F
		for _ in range(log.tracelength):
			print("Kin= "+str(hex(Kin))+' Din= '+str(hex(Din)))
			await log.logResult(Driver(Kin,Din,watch_point_handleinfo.handle),a._name)
			Din=Din^(1<<random.randint(0,127))
			Kin=Kin^(1<<random.randint(0,127))
			#print(log.log[a._name].BitVector)
	log.printLog()

	y=log.getDistribution()
	fig, ax = plt.subplots()
	x=range(128)
	ax.bar(x, y, width=1, edgecolor="white", linewidth=0.7)
	plt.show()
	
	
