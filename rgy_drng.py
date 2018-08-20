import __main__
if "itp" not in dir(__main__):
   import sys
   sys.path.append(r'C:\Intel\DAL')
   import itpii
   itp=itpii.baseaccess()
else:
   itp = __main__.itp


import components.socket as ss
socket_list=ss.getAll()
soc=socket_list[0]



#import itpii
from itpii.datatypes import BitData
#itp = itpii.baseaccess()
import time

class rgy_drng:
#class gen_drng:
    def __init__(self, chip="RGY"):
        self.chips = ['CHV','SKL','RGY']
        if chip in self.chips:
            pass
        else:
            print "Error, chip %d not supported"
            print "Using CHV instead"
            self.chip="CHV"
        self.partno=0    
        self.opmodenames=['normal','raw_bypass','deterministic_lfsr','deterministic_nines','raw_to_ob','PSMI','cheap_reset','no_bist','JFW']
        self.opmode={'normal':0,
                     'raw_bypass':1,
                     'deterministic_lfsr':2,
                     'deterministic_nines':3,
                     'raw_to_ob':4,
                     'PSMI':5,
                     'cheap_reset':6,
                     'no_bist':7,
                     'JFW':8}
        self.chip = chip
        self.clockcount=0
        if self.chip=="CHV":
            self.addr_getdata = 0x10
            self.addr_status = 0x14
            self.addr_config = 0x34
            self.addr_tpin = 0x38
            self.addr_tpout = 0x3c
            self.addr_esconfig = 0x40
            self.addr_getdata24 = 0x18
            self.addr_egetdata24 = 0x1C
        if self.chip=="SKL":
            self.addr_getdata = 0x4E20
            self.addr_getdata1 = 0x4E60
            self.addr_egetdata = 0x4E80
            self.addr_egetdata1 = 0x4EC0        
            self.addr_status = 0x4E00
            self.addr_config = 0x4E00 # config and status are merged in SKL
            self.addr_tpin = 0x4E08
            self.addr_tpout = 0x4E10
            self.addr_esconfig = 0x4E18
            self.addr_getdata24 = 0x4E14
            self.addr_egetdata24 = 0x4E1C
            self.addr_gti_status = 0x4E70
            self.addr_gti_rnfifo = 0x4E78
        if self.chip=="RGY":
            self.addr_getdata    = 0x0
            self.addr_getdata0   = 0x0
            self.addr_getdata1   = 0x1
            self.addr_status     = 0x2
            self.addr_config     = 0x3
            self.addr_tpin       = 0x4
            self.addr_tpout      = 0x5
            self.addr_esconfig   = 0x6
            self.addr_rracc_ctl  = 0x7
            self.addr_rracc_rac  = 0x8
            self.addr_dbgacc_ctl = 0x9
            self.addr_dbgacc_rac = 0xa
            self.addr_dbgacc_wac = 0xb
            self.addr_acc_cfg    = 0xc
            self.addr_acc_viol   = 0xd
            #Use the 2 lines 
            self.gd_size = 0x0
            self.gd_size = soc.drng.dgetdata0.getaddress()
            self.gd_size.curr_addr.size=0x4
    def read_reg(self,offset,quiet=0):
        if (self.chip=='CHV'):
            write_data = BitData(57, (6 << 54) | (0xF << 50) | ((0x100 + offset) << 2))
            itp.irdrscan('CHT_FUSE0', 0x30, 57, None, write_data)
            read_data = itp.irdrscan('CHT_FUSE0', 0x31, 34)
            while read_data[1:0] == 0:
                read_data = itp.irdrscan('CHT_FUSE0', 0x31, 34)
            if read_data[1:0] != 1:
                print "Error doing indirect JTAG access read transaction"
                return
            return read_data[33:2]
        elif (self.chip=='SKL'):
            data=itp.ucrb(0,offset)
            return data
        elif (self.chip=='RGY'):
            # Put in RGY CR read here
            #print "In Read Register with offset ", offset
            #print "Register Value for ", soc.drng.registers[offset], "=",soc.drng.readregister(soc.drng.registers[offset])
            return soc.drng.readregister(soc.drng.registers[offset])
            
    def read_reg64(self,offset,quiet=0):
        if (self.chip=='CHV'):
            pass
        elif (self.chip=='RGY'):
            # Put in RGY CR read here
            self.gd_size.curr_addr.size=0x8
            getdata64 = soc.drng.readregister(soc.drng.registers[offset])
            self.gd_size.curr_addr.size=0x4
            return getdata64
        else:
            data=itp.ucrb64(0,offset)
            return data
    def write_reg(self,offset, data,quiet=0):
        if (self.chip=='CHV'):
            write_data = BitData(57, (6 << 54) | (0xF << 50) | (data << 18) | ((0x100 + offset) << 2) | (1 << 1))
            itp.irdrscan('CHT_FUSE0', 0x30, 57, None, write_data)
            read_data = itp.irdrscan('CHT_FUSE0', 0x31, 34)
            while read_data[1:0] == 0:
                read_data = itp.irdrscan('CHT_FUSE0', 0x31, 34)
            if read_data[1:0] != 2:
                print "Error doing indirect JTAG access write transaction"
        elif (self.chip=='SKL'):
            itp.ucrb(0,offset,data)
        elif (self.chip=='RGY'):
            # Put in RGY CR write here
            return soc.drng.writeregister(soc.drng.registers[offset], data)

    def tp_enter(self):
        #itp.ucrb(0,0x4e08,0x00000006)
        self.write_reg(self.addr_tpin,0x00000006)
    
    def tp_exit(self):
        #itp.ucrb(0,0x4e08,0x00000007)   
        self.write_reg(self.addr_tpin,0x00000007)
    
    def tp_read(self,addr,quiet=0):
        if (addr > 0x602):
            print "Address %X out of range 0x000 - 0x602"
        else:
            thecommand = int((addr << 4) | 0x05)
            self.write_reg(self.addr_tpin,thecommand)
            preresult = self.read_reg(self.addr_tpout)
            # low 16 bits are the read data
            theresult = preresult & 0xffff
            leveled_dtack = 0
            if preresult & 0x010000 == 0x010000:
                leveled_dtack = 1
            # do something with leveled_dtack here..
        if (quiet==0):
            print "  Addr %X == 0x%04X (dtack=%d)" % (addr,theresult,leveled_dtack)
        return theresult
    def tp_write(self,addr,data,quiet=0):
        if (addr > 0x602):
            if (quiet==0):
                print "Address %X out of range 0x000 - 0x602"
        else:
            thecommand = int((data <<16) | (addr << 4) | 0x02)
            #itp.ucrb(0,0x4e08,thecommand)
            self.write_reg(self.addr_tpin,thecommand,quiet=quiet)
    def tp_set(self,addr,data,quiet=0):
        if (addr > 0x602):
            if (quiet==0):
                print "Address %X out of range 0x000 - 0x602"
        else:
            thecommand = int((data <<16) | (addr << 4) | 0x03)
            #itp.ucrb(0,0x4e08,thecommand)
            self.write_reg(self.addr_tpin,thecommand,quiet=quiet)
    def tp_reset(self,addr,data,quiet=0):
        if (addr > 0x602):
            print "Address %X out of range 0x000 - 0x602"
        else:
            thecommand = int((data <<16) | (addr << 4) | 0x04)
            #itp.ucrb(0,0x4e08,thecommand)
            self.write_reg(self.addr_tpin,thecommand)
    def tp_step(self,count=1,quiet=0):
        self.clockcount+=count
        if ((count > 0xffff) or (count < 0)):
            print "Count %X out of range 0x000 - 0xffff"
        else:
            thecommand = int((count << 16) | 0x0001)
            #itp.ucrb(0,0x4e08,thecommand) 
            self.write_reg(self.addr_tpin,thecommand)      
    def tp_nofm(self):
        #self.tp_enter()
        nofm=[]
        for i in xrange(0,16):
            towrite = 0x00004005 + (i << 4)
            #itp.ucrb(0,0x4e08,towrite)
            self.write_reg(self.addr_tpin,towrite)
            print "Writing TP %04X" % towrite
            #nofm=itp.ucrb(0,0x4e10)
            nofm=self.read_reg(self.addr_tpout)
            print "%04X" % nofm
        #self.tp_exit()
    def set_mode(self,quiet=0,opmode=0,fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=1):
        themode = 0x00000000
        if reset==1:
            themode = 0x00004000
        if (opmode >= 0) and (opmode < 8):
            themode = themode | (opmode << 4)
        if (fips == 1):
            themode = themode | 0x0100
        if (enable_scanout == 1):
            themode = themode | 0x00010000
        if (disable_clk_gating == 1):
            themode = themode | 0x00020000
        if (disable_ncu_buf == 1):
            themode = themode | 0x00040000      
        if (clear_aon_on_reset == 1):
            themode = themode | 0x00080000    
        themodeint = int(themode)      
        self.write_reg(self.addr_config,themode)
        returned = self.read_reg(self.addr_status)
        if (quiet==0):
            print "DRNG:Writing %08X to DRNG_Config" % themode
            print "DRNG:    Got %08X back status" % returned
    def set_esconfig(self,quiet=0, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0):
        theconfig = 0x00000000
        if (n >= 0) and (n < 256):
            theconfig = (theconfig & 0xffffff00) | (n & 0xff)
        if noxor==1:
            theconfig = (theconfig | 0x00000100)
        if nostop==1:
            theconfig = (theconfig | 0x00000200)
        if del_pace==1:
            theconfig = (theconfig | 0x00000400)
        if stop==1:
            theconfig = (theconfig | 0x00000800)
        if startup==1:
            theconfig = (theconfig | 0x00001000)
        if medium==1:
            theconfig = (theconfig | 0x00002000)
        if large==1:
            theconfig = (theconfig | 0x00004000)
        if exlarge==1:
            theconfig = (theconfig | 0x00008000)
        theconfigint = int(theconfig)      
        self.write_reg(self.addr_esconfig,theconfig)
        returned = self.read_reg(self.addr_esconfig)
        if (quiet==0):
            print "DRNG:Writing %04X to DRNG_ESCONFIG" % theconfig
            print "DRNG:    Got %08X back" % returned
    def read_status(self,quiet=0):
        thestatus = self.read_reg(self.addr_status)
        if (quiet==0):
            print "DRNG_STATUS:%08X" % thestatus
        bist_done = int((thestatus & 0x0001))
        bist_es_good = int((thestatus & 0x0004) >> 2)
        bist_kat_good = int((thestatus & 0x0008) >> 3)
        fips_out = int(((thestatus & 0x2000) >> 13))
        opmode_out = int(((thestatus & 0x1E00) >> 9))
        enable_scanout = int(((thestatus & 0x00010000) >> 16))
        disable_clk_gating = int(((thestatus & 0x00020000) >> 17))
        disable_ncu_buf = int(((thestatus & 0x00040000) >> 18))
        clear_aon_on_reset = int(((thestatus & 0x00080000) >> 19))
        thename = self.opmodenames[opmode_out]
        if (quiet==0):
            print "             opmode:%s" % thename
            print "               fips:%d" % fips_out
            print "          bist_done:%d" % bist_done
            print "       bist_es_good:%d" % bist_es_good
            print "      bist_kat_good:%d" % bist_kat_good   
            print "     enable_scanout:%d" % enable_scanout
            print " disable_clk_gating:%d" % disable_clk_gating
            print "    disable_ncu_buf:%d" % disable_ncu_buf
            print " clear_aon_on_reset:%d" % clear_aon_on_reset
        return thestatus
    def read_data32(self,amount=1,quiet=0):
        for i in xrange(0,amount):
            data = self.read_reg(self.addr_getdata)
            if (quiet==0):
                print "%08X" % data
        return data
    def read_data64(self,amount=1,quiet=0):
        outlist=list()
        if self.chip=='CHV':
            for i in xrange(0,amount):
                data = self.read_reg(self.addr_getdata)
                data2 = self.read_reg(self.addr_getdata)
                if (amount > 1):
                    outlist.append((data2,data))
                if (quiet==0):
                    print "%08X%08X" % (data2,data)
            if (amount > 1):
                return outlist
            else:
                return data2,data
        elif self.chip=='SKL':
            for i in xrange(0,amount):
                ldata = itp.ucrb64(0,self.addr_getdata)
                if (amount > 1):
                    outlist.append(ldata)
                if (quiet==0):
                    print "%016X" % (ldata)
            if (amount > 1):
                return outlist
            else:
                return ldata
        else:
            for i in xrange(0,amount):
                ldata = self.read_reg64(self.addr_getdata)
                if (amount > 1):
                    outlist.append(ldata)
                if (quiet==0):
                    print "%016X" % (ldata)
            if (amount > 1):
                return outlist
            else:
                return ldata

    def dumpbits(self,words=16):
        for i in xrange(0,16):
            theword = self.read_reg(self.addr_getdata)
            theword2 = self.read_reg(self.addr_getdata)
            theword = theword + (theword2 << 32)
            thewordstring=""
            for j in (0,64):
                if ((theword & 0x1) == 0x1):
                    thewordstring=thewordstring+"1"
                else:
                    thewordstring=thewordstring+"0"
                theword = theword >> 1
        print thewordstring

    def dumphex(self,dwords=64):
        for i in xrange(dwords):
            value = self.read_reg(0x10)
            print "%08X" % value

    def clock_and_dump(self,length, alist):
        for i in xrange(length):
            self.tp_step(1)
            for addr in alist:
                self.tp_read(addr)
            print ""
    def osteb(self):
        self.tp_enter()
        valreg=self.tp_read(0x322, quiet=1)

    # Force correct health count into health_count register. Health count will
    # remain correct until the following reset.
    def fix_health_count(self,quiet=0):
        self.tp_enter()
        m=list()
        # Read in the MofN delay line in DRBG validation block
        for i in xrange(16):
            value = self.tp_read(0x400+i,quiet=quiet)
            m.append(value)
            
        # Count the ones in it - convert to hex and use the count_bias function
        hexm = ""
        for i in xrange(16):
            hexm = hexm+("%04X" % m[i])
        
        (ones,bits,ratio) = self.count_bias(hexm)
        if (bits != 256):
            print "ERROR: fix_health_count, total bits must be 256, not %d." % bits
            self.tp_exit()
            exit(1)
            
        # Write the correct health count into health_count in validation block      
        correct_health_count = ones & 0x1FF
        if (quiet==0):
            print "Writing %04X to health_count." % correct_health_count
        self.tp_write(0x410,correct_health_count,quiet=quiet)
        self.tp_exit()
        
    def read_health_count(self,dataqty=100):
        health_count_list = list()
        health_count_nostop_list = list()
        valctl_list = list()
        valctl_nostop_list = list()
        c_list = list()
        c_nostop_list = list()
        self.drng_force_ro_clock()
        self.set_esconfig(nostop=0,n=0x00,exlarge=0,large=0,del_pace=1)
        self.set_mode(opmode=7, fips=0,reset=1,clear_aon_on_reset=1)
        self.fix_health_count(quiet=1)
        
        for i in xrange(10):
        
            self.read_data64(dataqty,quiet=1)
            self.tp_enter()
            hc_reg=(self.tp_read(0x410,quiet=1) & 0x01ff)
            valctl_list.append(self.tp_read(0x300,quiet=1))
            health_count_list.append(self.tp_read(0x410,quiet=1))
            c_list.append(self.tp_read(0x162,quiet=1))
            self.tp_exit()
            
        self.set_esconfig(nostop=1,n=0x00,exlarge=1,large=1,del_pace=1)
        self.set_mode(opmode=7, fips=0,reset=1,clear_aon_on_reset=1)
        self.fix_health_count(quiet=1)
        
        for i in xrange(10):
            self.read_data64(dataqty,quiet=1)
            self.tp_enter()
            health_count_nostop_list.append(self.tp_read(0x410,quiet=1))
            valctl_nostop_list.append(self.tp_read(0x300,quiet=1))
            c_nostop_list.append(self.tp_read(0x162,quiet=1))
            self.tp_exit()
        
        astring = ""
        bstring = ""
        for i in xrange(10):
            astring=astring+(" %03X " % health_count_nostop_list[i])   
        for i in xrange(10):
            bstring=bstring+(" %04X" % valctl_nostop_list[i])
        print "WITH NOSTOP, Health count was %s" % astring
        print "             Val CTL      was %s" % bstring
        astring = ""
        bstring = ""
        for i in xrange(10):
            astring=astring+(" %03X " % health_count_list[i])
        for i in xrange(10):
            bstring=bstring+(" %04X" % valctl_list[i])
        print "WITH   STOP, Health count was %s" % astring
        print "             Val CTL      was %s" % bstring
    
    
    def ascii_to_count(self,a):
            if a=='0':
                return (True,0)
            if a=='1':
                return (True,1)
            if a=='2':
                return (True,1)
            if a=='3':
                return (True,2)
            if a=='4':
                return (True,1)
            if a=='5':
                return (True,2)
            if a=='6':
                return (True,2)
            if a=='7':
                return (True,3)
            if a=='8':
                return (True,1)
            if a=='9':
                return (True,2)
            if a=='a':
                return (True,2)
            if a=='b':
                return (True,3)
            if a=='c':
                return (True,2)
            if a=='d':
                return (True,3)
            if a=='e':
                return (True,3)
            if a=='f':
                return (True,4)
            if a=='A':
                return (True,2)
            if a=='B':
                return (True,3)
            if a=='C':
                return (True,2)
            if a=='D':
                return (True,3)
            if a=='E':
                return (True,3)
            if a=='F':
                return (True,4)
            return (False,0)
    
    def count_bias(self,str):
        bits=0
        total=0
        for c in str:
            (good,count) = self.ascii_to_count(c)
            if (good==True):
                total += count
                bits+=4
        bias=float(total)/float(bits)
        return (total,bits,bias)
    
    def dump_oste(self,show_bias=0,prefix="",quiet=0):
        oste=list()
        nstr=""
        for i in xrange(16):
            value=self.tp_read(0x310+i,quiet=1)
            nstr = nstr+("%04X" % value)
        if (show_bias==1):
            (ones,bits,ratio)=self.count_bias(nstr)
            nstr=nstr+(" Bias = %d/%d = %f" % (ones,bits,ratio))
        self.drng_print(prefix+"OSTEB:"+nstr)
    
    def dump_oste128(self,show_bias=0, prefix=""):
        oste=list()
        nstr=prefix
        for i in xrange(8):
            value=self.tp_read(0x310+i,quiet=1)
            nstr = nstr+("%04X" % value)
        retval=nstr
        if (show_bias==1):
            (ones,bits,ratio)=self.count_bias(nstr)
            nstr=nstr+(" Bias = %d/%d = %f" % (ones,bits,ratio))
        self.drng_print("DRNG_SCREEN: OSTEB:"+nstr)
        return retval
        
    def dump_ob(self,matchstr,show_bias=0, prefix=""):
        success=False
        oste=list()
        nstr=prefix
        for i in xrange(8):
            value=self.tp_read(0x000+i,quiet=1)
            nstr = nstr+("%04X" % value)
        if (show_bias==1):
            (ones,bits,ratio)=self.count_bias(nstr)
            nstr=nstr+(" Bias = %d/%d = %f" % (ones,bits,ratio))
        if nstr==matchstr:
            nstr = nstr+" <-- Match"
            success=True
        print "OB:   "+nstr
        return success
        
    def find_healthy_count(self,quiet=0, show_bias=0, start_clock=1000, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0, opmode=0,fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=0):
        self.set_esconfig(quiet=quiet, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0)
        self.set_mode(opmode=0,quiet=quiet, fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=1)
        self.tp_enter()
        self.tp_write(0x600,0,quiet=quiet)
        found_phase1=False
        timeout=False
        i =0
        while (found_phase1 == False) and (timeout==False):
            i+=1
            self.tp_step(1000)
            time.sleep(0.05)
            bist_ctl2 = self.tp_read(0x501,quiet=1)
            time.sleep(0.05)
            if (bist_ctl2 & 0x2000)==0x2000:
                found_phase1=True
            if i > 100:
                timeout=True
        
        if timeout==True:
            if (quiet==0):
                self.drng_print("DRBG_SCREEN: Timeout Waiting for Phase 1 BIST")
            exit(1)
    
        i=0
        timeout=False
        found_cycle240=0
        remaining_clocks=start_clock
        while start_clock > 0x0f000:
            self.tp_step(0xf000)
            time.sleep(0.1)
            remaining_clocks=remaining_clocks-0xf000
        self.tp_step(remaining_clocks)
        time.sleep(0.1)
        
        while (found_cycle240 == False) and (timeout==False):
            i+=1
            self.tp_step(100)
            time.sleep(0.05)
            phase1_count=self.tp_read(0x503,quiet=1) & 0x3ff
            if (quiet==0):
                self.drng_print("phase1_count=%d" % phase1_count)
            if phase1_count > 240:
                found_cycle240 = True
            if i > 200:
                timeout=True
                
        if timeout==True:
            if (quiet==0):
                self.drng_print("DRNG_SCREEN: Timeout Waiting for phase1_count > 240, %d clocks" % (200*i))
            exit(1)            
        
        healthy_count = self.tp_read(0x500, quiet=quiet) & 0x7FF
        self.tp_read(0x100,quiet=quiet)
        healthy_count = self.tp_read(0x500, quiet=quiet) & 0x7FF
        if (quiet==0):
            self.drng_print("DRNG_SCREEN: Healthy Count at phase1_count=% is %02X" % (phase1_count, healthy_count))
        clocks=start_clock+(i*100)
        self.drng_print("DRNG_SCREEN: At clocks offset %d" % clocks)
        self.dump_oste(show_bias=1, prefix="DRNG_SCREEN: ")
        self.dump_oste(show_bias=1, prefix="DRNG_SCREEN: ")
        self.tp_step(0xffff)
        self.tp_exit()
        status=self.read_status(quiet=quiet)
        if quiet==1:
            self.drng_print("DRNG_SCREEN: Healthy Count = 0x%02X" % healthy_count)
            self.drng_print("DRNG_SCREEN: phase1_count  = 0x%02X" % phase1_count)
            self.drng_print("DRNG_SCREEN: status=%08X" % status)

    def health_count_track(self,qty=20, quiet=1, opmode=0, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0):
        self.set_esconfig(quiet=quiet, n=n,noxor=noxor,nostop=nostop,del_pace=del_pace,stop=stop,startup=startup,medium=medium,large=large, exlarge=exlarge)
        self.set_mode(quiet=1, fips=0)
        self.fix_health_count()
        for i in xrange(qty):
            self.read_data64(10,quiet=1)
            self.tp_enter()
            hc_reg=(self.tp_read(0x410,quiet=1) & 0x01ff)
            self.tp_exit()
            print "Health_count = 0x%03X" % hc_reg

        
    def health_count_quickcheck(self,quiet=1, opmode=0, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0):
        self.set_esconfig(quiet=quiet, n=n,noxor=noxor,nostop=nostop,del_pace=del_pace,stop=stop,startup=startup,medium=medium,large=large, exlarge=exlarge)
        self.set_mode(quiet=1, fips=0)
        self.fix_health_count()
        self.tp_enter()
        self.write_reg(0x600,(opmode << 5),quiet=1)
        self.tp_step(2)        
        self.tp_write(0x410,0x0100,quiet=1)
        self.tp_step(0xffff)
        self.tp_step(0xffff)
        hc_reg=(self.tp_read(0x410,quiet=1) & 0x01ff)
        self.tp_exit()
        return hc_reg
        
    def healthy_count_quickcheck(self,quiet=0, show_bias=0, start_clock=1000, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0, opmode=0,fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=0):
        self.set_esconfig(quiet=quiet, n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0)
        self.set_mode(opmode=0,quiet=quiet, fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=1)
        self.tp_enter()
        self.tp_write(0x600,0,quiet=quiet)
        found_phase1=False
        timeout=False
        i =0
        while (found_phase1 == False) and (timeout==False):
            i+=1
            self.tp_step(1000)
            time.sleep(0.05)
            bist_ctl2 = self.tp_read(0x501,quiet=1)
            time.sleep(0.05)
            if (bist_ctl2 & 0x2000)==0x2000:
                found_phase1=True
            if i > 100:
                timeout=True
        
        if timeout==True:
            self.drng_print("DRBG_SCREEN: Timeout Waiting for Phase 1 BIST")
            return -1
        
        i=0
        timeout=False
        found_cycle240=0
        remaining_clocks=start_clock
        while start_clock > 0x0f000:
            self.tp_step(0xf000)
            time.sleep(0.1)
            remaining_clocks=remaining_clocks-0xf000
        self.tp_step(remaining_clocks)
        time.sleep(0.1)
        
        while (found_cycle240 == False) and (timeout==False):
            i+=1
            self.tp_step(100)
            time.sleep(0.05)
            phase1_count=self.tp_read(0x503,quiet=1) & 0x3ff
            if (quiet==0):
                self.drng_print("phase1_count=%d" % phase1_count)
            if phase1_count > 240:
                found_cycle240 = True
            if i > 200:
                timeout=True
                
        if timeout==True:
            self.drng_print("DRNG_SCREEN: Timeout Waiting for phase1_count > 240, %d clocks" % (200*i))
            return -1
        
        healthy_count = self.tp_read(0x500, quiet=quiet) & 0x7FF
        self.tp_read(0x100,quiet=quiet)
        healthy_count = self.tp_read(0x500, quiet=quiet) & 0x7FF
        if (quiet==0):
            self.drng_print("DRNG_SCREEN: Healthy Count at phase1_count=% is %02X" % (phase1_count, healthy_count))
        self.tp_exit()
        status=self.read_status(quiet=quiet)
        if quiet==1:
            return healthy_count
            
    def match_oste_with_raw(self,show_bias=0,n=128,noxor=0,nostop=0,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0, opmode=4,fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=1):
        self.set_esconfig(n=128,noxor=noxor,nostop=nostop,del_pace=del_pace,stop=stop,startup=startup,medium=medium,large=large, exlarge=exlarge)
        self.set_mode(opmode=4,fips=0,reset=1,enable_scanout=enable_scanout,disable_clk_gating=disable_clk_gating,disable_ncu_buf=disable_ncu_buf,clear_aon_on_reset=clear_aon_on_reset)
        self.read_data64(10,quiet=1)
        self.tp_enter()
        matchstr=self.dump_oste128(show_bias=1)
        for i in xrange(10):
            self.dump_ob(matchstr, show_bias=show_bias)
            self.tp_set(0x600,0x400) # hit toto bit
            self.tp_step(2)
        self.tp_exit()
    
    def bist_time(self):
        self.set_mode(fips=0,quiet=1)
        self.tp_enter()
        self.tp_write(0x600,0,quiet=1)
        self.tp_step(5000)
        bist_ctl2=self.tp_read(0x501,quiet=1)
        i=0
        while (bist_ctl2 & 0x20)==0x00:
            self.tp_step(1000)
            bist_ctl2=self.tp_read(0x501,quiet=1)
            i+=1
        self.tp_exit()
        self.drng_print("DRNG_SCREEN: BIST TIME < %d clocks" % (5000+(i*1000)))
        
    def drng_reset_bist_time(self,):
        self.set_mode(fips=0,quiet=1)
        i =0
        timeout=0
        while True:
            i += 1
            #time.sleep(1)
            status=self.read_status(quiet=1)
            if (status & 0x0f) != 0x00:
                print "status = %08X on iteration %d" % (status,i)
                break
            if i > 10:
                timeout=1
        if timeout==1:
            print "timeout"
    
    def drng_force_ro_clock(self,enable=True):
        if self.chip == 'CHV':
            if enable==True:
                itp.irdrscan('CHT_FUSE0', 0x36, 32, None, BitData(32, 0x1))
            else:
                itp.irdrscan('CHT_FUSE0', 0x36, 32, None, BitData(32, 0x0))
    
    def drng_print(self,string):
        if self.partno==0:
            print string
        else:
            print "Writing to file :"+string
            string = string + "\n"
            self.f1.write(string)

    def logic_analyzer(self,opmode=0,stepsize=100):
        if (self.chip=='CHV'):
            self.drng_force_ro_clock()
        self.set_mode(opmode=opmode,fips=0)
        self.set_esconfig(nostop=1)
        self.tp_enter()
        self.tp_write(0x600,opmode<<5)
        self.clockcount=0
        #self.tp_step(2)
        print "clk  entropy drng lfsr     vlctl vlsm bistctl bistctl2 p0cnt p1cnt pausecnt crc      drbg drbg2 health_count oste buffa"
        for i in xrange(5000):
            buffa=self.tp_read(0x000,quiet=1)
            
            drbgctl=self.tp_read(0x160,quiet=1)
            drbgctl2=self.tp_read(0x161,quiet=1)
            
            oste = self.tp_read(0x300,quiet=1)
            valctl=self.tp_read(0x320,quiet=1)
            entropy = self.tp_read(0x321,quiet=1)
            valsm=self.tp_read(0x322,quiet=1)
            lfsrl=self.tp_read(0x323,quiet=1)
            lfsrh=self.tp_read(0x324,quiet=1)

            health_count=self.tp_read(0x410,quiet=1)
            
            bistctl=self.tp_read(0x500,quiet=1)
            bistctl2=self.tp_read(0x501,quiet=1)
            p0count=self.tp_read(0x502,quiet=1)
            p1count=self.tp_read(0x503,quiet=1)
            pausecount=self.tp_read(0x504,quiet=1)
            crcl=self.tp_read(0x505,quiet=1)
            crch=self.tp_read(0x506,quiet=1)
            
            drngctl=self.tp_read(0x600,quiet=1)
            
            print "%04x %04X    %04X %04X%04X %04X  %04X %04X    %04X     %04X  %04X  %04X     %04X%04X %04X %04X  %04X         %04X %04X" % \
             (self.clockcount,entropy,drngctl,lfsrh,lfsrl,valctl,    valsm,    bistctl,     bistctl2,      p0count,    p1count,    pausecount,    crch,crcl,drbgctl,drbgctl2,health_count,oste,buffa)
            self.tp_step(stepsize)

    def read_kat_crc(self):
        self.drng_force_ro_clock()
        self.set_mode(fips=0)
        self.tp_enter()
        crcl = self.tp_read(0x505) & 0x000ffff
        crch = self.tp_read(0x506)
        crch = (crch << 16) & 0xffff0000
        crc = crch | crcl
        print "KAT CRC = %08X" % crc
        
    def drng_screen(self,partno=0,number_of_ostes=1):
        self.partno = partno
        if (self.partno > 0):
            filename = "drng_fuse.log"
            path = "M:\\Products\\Cherryview\\Power-On\\Screening\\"
            fullname = path+filename
            self.f1 = open(fullname,'a')
        self.drng_force_ro_clock(enable=True)
        
        if (self.partno > 0):
            self.drng_print("")
        self.drng_print("DRNG_SCREEN: Start Screen PARTNO %d" % partno)
        
        status1 = self.read_status(quiet=1) # power on status
        self.set_esconfig(quiet=1)
        
        self.set_mode(quiet=1,fips=1)
        time.sleep(0.1)
        status2 = self.read_status(quiet=1) # post local reset status
        
        self.set_mode(quiet=1,fips=0)
        self.tp_enter()
        self.tp_write(0x600,0,quiet=1)
        self.tp_step(17000)
        time.sleep(0.1)
        self.tp_exit()
        #for i in xrange(10):
        status3 = self.read_status(quiet=1)
        
        self.set_esconfig(n=128,quiet=1, noxor=0,nostop=1,del_pace=1,stop=0,startup=0,medium=1,large=0, exlarge=0)
        self.set_mode(quiet=1, opmode=4,fips=0,reset=1,enable_scanout=0,disable_clk_gating=0,disable_ncu_buf=1,clear_aon_on_reset=1)
        
        self.read_data64(10,quiet=1)
        self.tp_enter()
        
        if (status1 & 0x000f) == 0x000f:
            self.drng_print("DRNG_SCREEN: power on   status passed    status=%08X" % status1)
        elif (status1 & 0x000f) == 0x0009:
            self.drng_print("DRNG_SCREEN: power on ES Fail, KAT pass  status=%08X" % status1)
        elif (status1 & 0x000f) == 0x0000:
            self.drng_print("DRNG_SCREEN: power on BIST not complete  status=%08X" % status1)
        else:
            self.drng_print("DRNG_SCREEN: Power on ???                status=%08X" % status1)
        
        if (status2 & 0x000f) == 0x000f:
            self.drng_print("DRNG_SCREEN: DRNG reset status passed    status=%08X" % status2)
        elif (status2 & 0x000f) == 0x0009:
            self.drng_print("DRNG_SCREEN: DRNG reset ES-Fail KAT-pass status=%08X" % status2)
        elif (status2 & 0x000f) == 0x0000:
            self.drng_print("DRNG_SCREEN: DRNG reset BIST not complete status=%08X" % status2)
        else:
            self.drng_print("DRNG_SCREEN: DRNG reset                  status=%08X" % status2)
            #oste_string2=dump_oste(show_bias=1,prefix = "DRNG_SCREEN: ")
        
        if (status3 & 0x000f) == 0x000f:
            self.drng_print("DRNG_SCREEN: DRNG TP    status passed    status=%08X" % status3)
        elif (status3 & 0x000f) == 0x0009:
            self.drng_print("DRNG_SCREEN: DRNG TP    ES-Fail KAT-pass status=%08X" % status3)
        elif (status3 & 0x000f) == 0x0000:
            self.drng_print("DRNG_SCREEN: DRNG TP   BIST not complete status=%08X" % status3)
        else:
            self.drng_print("DRNG_SCREEN: DRNG TP                     status=%08X" % status3)
            oste_string2=self.dump_oste(show_bias=1,prefix = "DRNG_SCREEN: ")

        number_of_ostes=number_of_ostes-1
        if number_of_ostes > 0:
            for i in xrange(number_of_ostes):
                self.tp_exit()
                self.read_data64(10,quiet=1)
                self.read_data64(10,quiet=1)
                self.tp_enter()    
                oste_string2=self.dump_oste(show_bias=1, prefix="DRNG_SCREEN: ",quiet=1)
        
        self.tp_exit()
        self.set_mode(quiet=1, fips=0)
        
        self.find_healthy_count(quiet=1)
        self.bist_time()
        self.drng_print("DRNG_SCREEN: End Screen")
        self.drng_force_ro_clock(enable=0)
        if (self.partno > 0 ):
            self.f1.close()

    def tp_read_128(self, start_addr):
        word = self.tp_read(start_addr)
        final_value = 0x0
        # 1..7 since we just did 0
        for i in range(1,8):
            # shift first to make space for what we're about to read
            final_value = final_value << 16
            # read 16 bits
            word = self.tp_read(start_addr + i)
            # OR it into the 16 LSBits
            final_value = final_value | word
            
        return final_value
    
# KAT (known answer test) for CAVS certification
# extend for future unknown answer test support
# basically starts the DRBG (including AES) in a known state and runs for 11 cycles and then collects the answer
    def cavs(self):
        self.set_mode(quiet=1,fips=0)
        self.tp_enter()
        
        # K (key)
        self.tp_read_128(0x100)
        # V (value)
        self.tp_read_128(0x120)
        # ce low (conditioned entropy low 128 bits)
        self.tp_read_128(0x130)
        # ce high (conditioned entropy high 128 bits)
        self.tp_read_128(0x140)
        # t1
        self.tp_read_128(0x150)
        # ctl
        self.tp_read(0x160)
        # ctl2
        self.tp_read(0x161)
        # c
        self.tp_read(0x162)

        #self.tp_write(0x600,0,quiet=1)
        #self.tp_step(17000)
        #time.sleep(0.1)
        
        self.tp_exit()

        
