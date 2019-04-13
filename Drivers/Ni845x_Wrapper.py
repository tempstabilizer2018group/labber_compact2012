import ctypes, os
import numpy as np
from ctypes import (c_int, c_uint8, c_int16, c_uint16, c_int32, c_uint32, 
                    c_char_p, byref)

# match naming conventions in DLL
int8 = c_int
uInt8 = c_uint8
int16 = c_int16
uInt16 = c_uint16
int32 = c_int32
uInt32 = c_uint32
#NiHandle = c_void_p 
NiHandle = c_uint32

# error type returned by this class
class Error(Exception):
    pass

# open dll
try:
    # if failure, try to open in driver folder
    sPath = os.path.dirname(os.path.abspath(__file__))
    DLL = ctypes.WinDLL('Ni845x')
except:
    raise
    print 'import dll from path'
    # if failure, try to open in driver folder
    sPath = os.path.dirname(os.path.abspath(__file__))
    DLL = ctypes.WinDLL(os.path.join(sPath, 'Ni845x'))


# helper function for calling DLL functions and checking errors
def callFunc(sFunc, *args, **kargs):
    """General function caller with restype=status, also checks for errors"""
    # get function from DLL
    func = getattr(DLL, sFunc)
    func.restype = int32
    # check keyword args
    bCheckError = kargs['check_error'] if 'check_error' in kargs else True 
    # call function, raise error if needed
    status = func(*args)
    if bCheckError:
        (error, message) = checkError(status)
        if error:
            raise Error(message)

#kNI845XExport void NI845X_FUNC ni845xStatusToString(
#   int32  StatusCode,
#   uInt32 MaxSize,
#   int8 * StatusString
#   );
def checkError(status):
    """Convert the error in status to tuple (error=False, message)"""
    # call function to convert status to string
    func = getattr(DLL, 'ni845xStatusToString')
    bufferLen = uInt32(1024)
    msgBuffer = c_char_p(' '*1024)
    func(int32(status), bufferLen, msgBuffer)
    # convert c str to python string
    message = str(msgBuffer.value).strip()
    return (status<0, message)


class NI845x():
    """Represent the NI USB 845x , redefines the dll functions in python"""

    def __init__(self, resource_name):
        """The init case defines a session ID, used to identify the instrument"""
        # create a session id
        self.handle = NiHandle()
        self.script = None
        # open communication
        self.ni845xOpen(resource_name)


    def closeConnection(self):
        """Close connection after finishing all operations"""
        # close open scripts first
        self.ni845xSpiScriptClose(last=True)
        self.ni845xClose()


#kNI845XExport int32 NI845X_FUNC ni845xOpen(
#   char *     ResourceName,
#   NiHandle * DeviceHandle
#   );
    def ni845xOpen(self, resource_name):
        callFunc('ni845xOpen', c_char_p(resource_name), byref(self.handle))


#kNI845XExport int32 NI845X_FUNC ni845xClose (
#   NiHandle DeviceHandle
#   );
    def ni845xClose(self):
        # close connection
        callFunc('ni845xClose', self.handle)


#kNI845XExport int32 NI845X_FUNC ni845xSetIoVoltageLevel(
#   NiHandle DeviceHandle,
#   uInt8    VoltageLevel
#   );
    kNi845x33Volts = 33 # 3.3V
    kNi845x25Volts = 25 # 2.5V
    kNi845x18Volts = 18 # 1.8V
    kNi845x15Volts = 15 # 1.5V
    kNi845x12Volts = 12 # 1.2V
    #
    def ni845xSetIoVoltageLevel(self, voltageLevel):
        # close connection
        callFunc('ni845xSetIoVoltageLevel', self.handle, uInt8(voltageLevel))


#kNI845XExport int32 NI845X_FUNC ni845xDioSetPortLineDirectionMap (
#   NiHandle DeviceHandle,
#   uInt8    PortNumber,
#   uInt8    Map
#   );
    def ni845xDioSetPortLineDirectionMap(self, port=0, lOutput=[0,0,0,0,0,0,0,0]):
        """Configure DIO port from list. 0 is input, 1 is output"""
        # convert list to binary pattern
        portMap = 0
        for n, bit in enumerate(lOutput):
            portMap += bit*2**n
        callFunc('ni845xDioSetPortLineDirectionMap', self.handle,
                 uInt8(port), uInt8(portMap))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptOpen (
#   NiHandle * ScriptHandle
#   );
    def ni845xSpiScriptOpen(self, first=False):
        # BUG FIX for long-time error: only open if first time, otherwise use old
        if self.script is None:
            self.script = NiHandle()
            callFunc('ni845xSpiScriptOpen', byref(self.script))
        # reset the script right after opening
        self.ni845xSpiScriptReset()


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptClose (
#   NiHandle ScriptHandle
#   );
    def ni845xSpiScriptClose(self, last=False):
        # BUG FIX for long-time error: only close script when closing the driver
        if last and self.script is not None:
            callFunc('ni845xSpiScriptClose', self.script)


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptRun (
#   NiHandle ScriptHandle,
#   NiHandle DeviceHandle,
#   uInt8    PortNumber
#   );
    def ni845xSpiScriptRun(self, port=0):
        callFunc('ni845xSpiScriptRun', self.script, self.handle, uInt8(port))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptReset (
#   NiHandle ScriptHandle
#   );
    def ni845xSpiScriptReset(self):
        callFunc('ni845xSpiScriptReset', self.script)


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptEnableSPI (
#   NiHandle ScriptHandle
#   );
    def ni845xSpiScriptEnableSPI(self):
        callFunc('ni845xSpiScriptEnableSPI', self.script)


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptDisableSPI (
#   NiHandle ScriptHandle
#   );
    def ni845xSpiScriptDisableSPI(self):
        callFunc('ni845xSpiScriptDisableSPI', self.script)


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptCSLow (
#   NiHandle ScriptHandle,
#   uInt32   ChipSelectNum
#   );
    def ni845xSpiScriptCSLow(self, chip=0):
        callFunc('ni845xSpiScriptCSLow', self.script, uInt32(chip))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptCSHigh (
#   NiHandle ScriptHandle,
#   uInt32   ChipSelectNum
#   );
    def ni845xSpiScriptCSHigh(self, chip=0):
        callFunc('ni845xSpiScriptCSHigh', self.script, uInt32(chip))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptClockPolarityPhase (
#   NiHandle ScriptHandle,
#   int32    ClockPolarity,
#   int32    ClockPhase
#   );
    kNi845xSpiClockPolarityIdleLow  = 0  # Idle Low
    kNi845xSpiClockPolarityIdleHigh = 1  # Idle High
    kNi845xSpiClockPhaseFirstEdge   = 0  # First Edge
    kNi845xSpiClockPhaseSecondEdge  = 1  # Second Edge
    def ni845xSpiScriptClockPolarityPhase(self, polarity=0, phase=1):
        callFunc('ni845xSpiScriptClockPolarityPhase', self.script,
                 int32(polarity), int32(phase))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptClockRate (
#   NiHandle ScriptHandle,
#   uInt16   ClockRate
#   );
    def ni845xSpiScriptClockRate(self, clockRate=100):
        """Set clock rate in kHz"""
        callFunc('ni845xSpiScriptClockRate', self.script, uInt16(clockRate))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptDelay (
#   NiHandle ScriptHandle,
#   uInt8    Delay
#   );
    def ni845xSpiScriptDelay(self, delay=1):
        """Add delay in milliseconds"""
        callFunc('ni845xSpiScriptDelay', self.script, uInt8(delay))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptUsDelay (
#   NiHandle ScriptHandle,
#   uInt16   Delay
#   );
    def ni845xSpiScriptUsDelay(self, delay=1):
        """Add delay in microseconds"""
        callFunc('ni845xSpiScriptUsDelay', self.script, uInt16(delay))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptDioConfigureLine (
#   NiHandle ScriptHandle,
#   uInt8    PortNumber,
#   uInt8    LineNumber,
#   int32    ConfigurationValue
#   );
    def ni845xSpiScriptDioConfigureLine(self, port=0, line=0, configValue=0):
        callFunc('ni845xSpiScriptDioConfigureLine', self.script, 
                 uInt8(port), uInt8(line), int32(configValue))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptDioWriteLine (
#   NiHandle ScriptHandle,
#   uInt8    PortNumber,
#   uInt8    LineNumber,
#   int32    WriteData
#   );
    def ni845xSpiScriptDioWriteLine(self, port=0, line=0, data=0):
        callFunc('ni845xSpiScriptDioWriteLine', self.script, 
                 uInt8(port), uInt8(line), int32(data))


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptDioReadLine (
#   NiHandle ScriptHandle,
#   uInt8    PortNumber,
#   uInt8    LineNumber,
#   uInt32 * ScriptReadIndex
#   );
    def ni845xSpiScriptDioReadLine(self, port=0, line=0):
        index = uInt32(0)
        callFunc('ni845xSpiScriptDioReadLine', self.script, 
                 uInt8(port), uInt8(line), byref(index))
        # convert and return index
        return index


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptWriteRead (
#   NiHandle ScriptHandle,
#   uInt32   WriteSize,
#   uInt8 *  WriteData,
#   uInt32 * ScriptReadIndex
#   );
    def ni845xSpiScriptWriteRead(self, data):
        """Write data from vector"""
        # create buffer with data
        writeData = (uInt8*len(data))()
        for n, a in enumerate(data):
            writeData[n] = uInt8(a)
        writeSize = uInt32(len(data))
        index = uInt32(0)
        callFunc('ni845xSpiScriptWriteRead', self.script, 
                 writeSize, byref(writeData), byref(index))
        # return data index
        return index
        

#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptExtractReadDataSize (
#   NiHandle ScriptHandle,
#   uInt32   ScriptReadIndex,
#   uInt32 * ReadDataSize
#   );
    def ni845xSpiScriptExtractReadDataSize(self, index):
        dataSize = uInt32(0)
#        dataSize = (uInt32*1)()
        callFunc('ni845xSpiScriptExtractReadDataSize', self.script, 
                 index, byref(dataSize))
        # return data size
        return int(dataSize.value)


#kNI845XExport int32 NI845X_FUNC ni845xSpiScriptExtractReadData (
#   NiHandle ScriptHandle,
#   uInt32   ScriptReadIndex,
#   uInt8 *  ReadData
#   );
    def ni845xSpiScriptExtractReadData(self, index):
        # find data size
        size = self.ni845xSpiScriptExtractReadDataSize(index)
        # create data buffer
        data = (uInt8*size)()
        callFunc('ni845xSpiScriptExtractReadData', self.script, 
                 index, byref(data))
        # convert data to list of integers
        lOut = [int(a) for a in data]
        return lOut



class ETH_Compact(NI845x):
    """Represents the ETH compact voltage source, using the NI USB 845x"""

    def __init__(self, resource_name, save_to_disk=False):
        """The init case defines a session ID, used to identify the instrument"""
        # init variables
        self.save_to_disk = save_to_disk
        self.chip = 0
        self.chipGeo = 1
        self.port = 0
        # keep track of values (10 voltages)
        self.lValue = np.zeros(10)
        # start with opening NI845x
        NI845x.__init__(self, resource_name)
        #
        # get file name for saving data
        if self.save_to_disk:
            sPath = os.path.dirname(os.path.abspath(__file__))
            self.sFile = os.path.join(sPath, ('Values-%s.txt' % str(resource_name)))
            # try to load old values
            self.loadValuesFromDisk()


    def loadValuesFromDisk(self):
        """Load values from disk"""
        try:
            # open and convert to numbers
            with open(self.sFile, 'r') as f:
                s = f.read()
            v = np.fromstring(s, sep=',')
            # make sure we have ten elements
            if len(v) == 10:
                self.lValue = v
        except Exception as e:
            # ignore errors
            print str(e)
            pass


    def saveValueToDisk(self):
        """Save current values to disk"""
        with open(self.sFile, 'w') as f:
            f.write(','.join([str(a) for a in self.lValue]))


    def setLED(self, value=True, iLED=5):
        """Set LED"""
        self.ni845xSpiScriptOpen()
        self.ni845xSpiScriptDioWriteLine(self.port, line=iLED, data=int(value))
        self.ni845xSpiScriptRun()
        self.ni845xSpiScriptClose()

    """ 
    This initialization function has been modified by Palm Marius on 18.08.2016
    Now, this function allows to distinct between two initialization modes:
        fullInitialize = True:  required after power up of compact
                                sets all values to 0
        fullInitialize = False: sufficient if compact is still on power 
                                but usb connection was powered off/disconnected

    Comment: the default value for fullInitialize is True for compatibility 
    reasons with the old code
    """
    def initialize(self,fullInitialize = True):
        """Set value to channel"""
        # configure device
        self.ni845xSetIoVoltageLevel(self.kNi845x33Volts)
        self.ni845xDioSetPortLineDirectionMap(port=self.port, lOutput=[1,0,0,0,0,1,1,1])
        # create script
        self.ni845xSpiScriptOpen(first=True)
        self.ni845xSpiScriptEnableSPI()
        #
        self.ni845xSpiScriptCSHigh(self.chip)
        # configure line 0 as output (=1)
        self.ni845xSpiScriptDioConfigureLine(self.port, line=0, configValue=1)
        # write logical 0 to line 0 (sync/init)
        self.ni845xSpiScriptDioWriteLine(self.port, line=0, data=0)
        # set clock polarity (low in idle, phase centered on second edge)
        self.ni845xSpiScriptClockPolarityPhase(polarity=self.kNi845xSpiClockPolarityIdleLow,
                                               phase=self.kNi845xSpiClockPhaseSecondEdge)
        # set clock rate (in kHz)
        self.ni845xSpiScriptClockRate(100)
        self.ni845xSpiScriptDelay(1)

        """ 
        Begin of the actual modification (see function header for descriptions)  
        """
        if fullInitialize == True:
            self.ni845xSpiScriptCSLow(self.chip)
            #
            # init output (using settings from VI)
            #23: 0 0:write 1:read 
            #22: 0 (Control Reg) 
            #21: 1 (Control Reg) 
            #20: 0 (Control Reg) 
            #19: 0 Reserved
            #18: 0 Reserved
            #17: 0 Reserved
            #16: 0 Reserved
            #15: 0 Reserved
            #14: 0 Reserved
            #13: 0 Reserved
            #12: 0 Reserved
            #11: 0 Reserved
            #10: 0 Reserved
            #9: 0 LIN COMP
            #8: 0 LIN COMP
            #7: 0 LIN COMP
            #6: 0 LIN COMP
            #5: 0 SDODIS
            #4: 1 BIN/2sC
            #3: 0 DACTRI
            #2: 0 OPGND
            #1: 1 RBUF
            #0: 0 Reserved
            # 
            # NB!! 3*10 bytes, data seems to be sent with MSB first
            lBytes = [0b00100000, 0b00000000, 0b00010010]*10
            self.ni845xSpiScriptWriteRead(lBytes)
            # sync operation
            self.sync()
            # set all values to zero
            self.lValue = np.zeros(10)
            self.copyValuesToDAC()
            # sync operation
            self.sync()
            self.ni845xSpiScriptCSHigh(self.chip)
        
        """
        End of the modifications
        """
        
        # run and close script
        self.ni845xSpiScriptRun()
        self.ni845xSpiScriptClose()


    def setValue(self, index=0, value=0.0, send_to_instr=True):
        """Set value to DAQ"""
        self.lValue[index] = value
        if send_to_instr:
            self.sendValues()


    def getValue(self, index=0):
        """Get value from memory"""
        return self.lValue[index]


    def sendValues(self):
        """Script for sending values to DAC"""
        # create script
        self.ni845xSpiScriptOpen() 
        self.ni845xSpiScriptCSLow(self.chip)
        # copy values to DAC
        self.copyValuesToDAC()
        # sync operation
        self.sync()
        self.ni845xSpiScriptCSHigh(self.chip)
        # run and close script
        self.ni845xSpiScriptRun()
        self.ni845xSpiScriptClose()


    def readGeophoneVoltage(self):
        """Read geophone voltage"""
        # create script
        self.ni845xSpiScriptOpen()
#        self.ni845xSpiScriptEnableSPI()
        #
        self.ni845xSpiScriptCSHigh(self.chipGeo)
        # set clock polarity (low in idle, phase centered on second edge)
        self.ni845xSpiScriptClockPolarityPhase(polarity=self.kNi845xSpiClockPolarityIdleLow,
                                               phase=self.kNi845xSpiClockPhaseSecondEdge)
        # set clock rate (in kHz)
        self.ni845xSpiScriptClockRate(100)
        self.ni845xSpiScriptDelay(10)
        self.ni845xSpiScriptCSLow(self.chipGeo)
        #
        # ask for two bytes by first sending two bytes
        indxRead = self.ni845xSpiScriptWriteRead([0, 0])
        self.ni845xSpiScriptCSHigh(self.chipGeo)
        self.ni845xSpiScriptRun()
        lOut = self.ni845xSpiScriptExtractReadData(indxRead)
        # convert to voltage, start by assemblying word
        word = np.int32(lOut[1] + 256*lOut[0])
        # shift one bit and filter out 12 bits of data
        data = np.bitwise_and(2**12-1, np.right_shift(word, 1))
        # gainINA103 = 1000, dividerR49R51 = 0.33,  VrefMCP3201 = 3.3 therefore VrefMCP3201/gainINA103/dividerR49R51 = 0.01
        voltage = 0.01 * (data/4096.0)
        # close script
        self.ni845xSpiScriptClose()
        return voltage


    def readGeophoneVelocity(self):
        """Read geophone voltage and convert to velocity"""
        voltage = self.readGeophoneVoltage()
        # datasheet RTC-10hz, 395ohm, at 1000 Ohm RL 19.7 V/(m/s)
        return voltage/19.7


    def sync(self):
        """Sync operation, write high then low"""
        self.ni845xSpiScriptDioWriteLine(self.port, line=0, data=1)
        self.ni845xSpiScriptDioWriteLine(self.port, line=0, data=0)


    def copyValuesToDAC(self):
        """Copy values to DAC"""
        # create list of i32 for handling data
        vInt = np.zeros(len(self.lValue), dtype=np.int32)
        for n, val in enumerate(self.lValue):
            vInt[n] = (val/10.0) * (2**19)
        # make sure data is within range
        vInt = np.clip(vInt, -2**19, (2**19) - 1)
        # convert to list of 10*3 bytes, reverse order to keep msb first
        vU32 = np.array(vInt[::-1] + 2**19, dtype=np.uint32) + 2**20
        vByte = np.zeros(3*len(vU32), dtype=np.uint8)
        for n, u32 in enumerate(vU32):
            # convert to 3 bytes, msb first
            vByte[n*3] = np.bitwise_and(255, np.right_shift(u32,16))
            vByte[n*3+1] = np.bitwise_and(255, np.right_shift(u32,8))
            vByte[n*3+2] = np.bitwise_and(255, u32)
        # write data
        self.ni845xSpiScriptWriteRead(vByte)
        # save to disk, if wanted
        if self.save_to_disk:
            self.saveValueToDisk()



if __name__ == '__main__':
    #
    import time
    # test driver
#    spi = NI845x('test')
#    print "Error", checkError(-301709)
    eth = ETH_Compact('8452')
#    eth = ETH_Compact('USB0::0x3923::0x7514::01A39834::RAW')
    t0 = time.time()
    eth.initialize()
    eth.setLED(False, 5)
    eth.setLED(False, 6)
    eth.setLED(False, 7)
    eth.setValue(2, -10)
    print 'Time: %.2f ms' % (1000*(time.time() - t0))
    eth.setValue(1, 3.8)
    print 'Time: %.2f ms' % (1000*(time.time() - t0))
    eth.setValue(0, 2)
    print 'Time: %.2f ms' % (1000*(time.time() - t0))
    time.sleep(1.0)
    print eth.readGeophoneVoltage()
    print eth.readGeophoneVoltage()
    print 'read volt: %.2f ms' % (1000*(time.time() - t0))
    eth.closeConnection()

    


