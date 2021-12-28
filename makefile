TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(shell pwd)/aes_tb.v $(shell pwd)/Syn_Custom_AES.v  $(shell pwd)/sc12_cmos10lpe_base_lvt.v
TOPLEVEL = testbench
MODULE = testbench

include $(shell cocotb-config --makefiles)/Makefile.sim
