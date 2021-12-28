`timescale 1 ns/1 ps
//`define functional 0
module testbench();

parameter HALF_CLK_PERIOD = 20;
 
//------------------------------------------------
   reg          CLK;   // System clock
   reg          RSTn;  // Reset (Low active)
   reg          EN;    // AES circuit enable
   reg  [127:0] Kin;   // Key input
   reg [127:0]  Din;   // Data input  
   reg          KDrdy; // Key/Data input ready
   string    st;
   reg[1:0]  string_sel;
//   reg          Drdy;
   
   wire [127:0] Dout; // Data output
   wire         Kvld; // Data output valid
   wire         Dvld; // Data output valid
   wire         BSY;  // Busy signal
   wire         trigger;  // trigger signal for Oscilloscope
 
   integer i,j;
   integer file1, file2, file3;

   // Temporary reg data to store the expected outputs
   reg [127: 0] REG_OUTPUT  [0: 999];

   //initial $sdf_annotate("./Syn_StdAES_Async.sdf", U1);

   Custom_AES U1 (//inputs
               .CLK(CLK), .RSTn(RSTn), .EN(EN), .Kin(Kin), .Din(Din), .KDrdy(KDrdy),    
               //outputs
               .Dout(Dout), .Kvld(Kvld), .Dvld(Dvld), .BSY(BSY), .trigger(trigger));


always@(*)
begin
	case(string_sel)
	0:
		st="N";
	1:
		st="F1";
	2:
		st="F0";
	default:
		st="?";
	endcase
end
initial
  begin 
   string_sel=0;
    CLK = 1;
    forever #HALF_CLK_PERIOD CLK = !CLK;
  end
initial begin
  $dumpfile ("test.vcd");
  $dumpvars (0, testbench);
  #1;
end
/*
initial 
 begin     
 //  $vcdpluson(U1); 
   EN    = 0;
   RSTn  = 0;
   KDrdy = 0;
//   Drdy = 0;
   Kin   = 0;
   Din   = 0;

   #(3*HALF_CLK_PERIOD);
   EN    = 1;
   RSTn  = 1;

   #(2*HALF_CLK_PERIOD);
   Kin  = 128'h000102030405060708090A0B0C0D0E0F;
   Din  = 128'h00112233445566778899AABBCCDDEEFF;

   KDrdy = 1;
   #(2*HALF_CLK_PERIOD);
   KDrdy = 0;

   for (i = 0; i < 4; i = i + 1)
   begin
     #(28*HALF_CLK_PERIOD);
     
     KDrdy = 1;
     #(2*HALF_CLK_PERIOD);
     KDrdy = 0;
     #(2*HALF_CLK_PERIOD); 
     Din = Dout; 

     #(4*HALF_CLK_PERIOD);

   end  
   $finish;  
   
end
*/
initial
  begin
    #(1000*2*HALF_CLK_PERIOD);
    $finish;
  end
endmodule
