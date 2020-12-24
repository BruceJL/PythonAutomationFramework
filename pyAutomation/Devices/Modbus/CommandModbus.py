from datetime import datetime
from pyAutomation.DataObjects.Point import Point
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
import re

address_regex = re.compile(r"(?P<register>\d+)\.(?P<bit>\d+)")

@staticmethod
def getCommandReplyLength(points: 'List<Point>'):
	""" Returns the length of the return data packet for a given
		group of commands."""
	if (len(points) > 1):
		length = \
			points[-1]['address'] \
			+ wordLength(points[-1]['datatype'])-1 \
			- points[0]['address']
	else:
		return dataLength(points[0]['dataType'])


@staticmethod
def dataLength(data_type: 'str') -> 'int':
	""" Get the data length in words for a given command data type"""
	if data_type == 'bit' or data_type == 'int16':
		return 1
	if data_type == 'int32' or data_type == 'float32':
		return 2
	if data_type == 'float64':
		return 4

@staticmethod
def nextRegister(point) -> 'bool':
	""" Returns the next register after this point that would be eligable to 
	hold another point. """
	return point['address']+ dataLength(point);


@staticmethod
def getMaxCommandReplySize(command: 'str') -> 'int':
	""" Get the maximum allowable number data points that can be returned 
	for a given command"""
	if command_type == 'BIT' or command_type == 'DISCRETE':
		max_size = 124*16
	elif command_type == 'HOLDING' or command_type == 'INPUT':
		max_size = 124
	else: 
		assert False, "Invalid command type specified."

@staticmethod
def makeCommandObjects(
	points: 'List[Dict[str, Any]]'
) -> 'List[CommandModbus]':
	""" Takes the points required for this driver and sorts them into 
	groups so that commands of nearby addresses are grouped together. This 
	allows the Modbus client to get the points form the server using a 
	minimum number of requests"""

	points = sorted(points, key = lambda i: i['address'], reverse=False) 

	mc = [] # type: List[CommandModbus]

	command_type = points[0]['command']
	command_datatype = points[0]['datatype']

	# get the total length of all the registers for this command type.
	command_reply_length = getCommandReplyLength(points)
	if length <= getMaxCommandReplySize(points):
		mc.append(CommandModbus(points))
		mc.buildCommandBytes()
		readCommands.add(mc)
	else:
		distances = [] # type: List[int]
		biggest_distance = 0  # type: int
		biggest_distance_index = 0 # type: int

		# Build an index of the distance between each command.
		for i in range(1, len(points)-1):
			distances.append(
				dataLength(points[i]['DataType']) 
				+ dataLength(points[i+1]['DataType'])
				- points[i]['address']
			)

		for i in range(1, len(distances)):
			if (distances[i] > biggest_distance_index):
				biggest_distance = distances[i]
				biggest_distance_index = i

		mc.append(makeCommandObjects(points[0:biggest_distance_index]))
		mc.append(makeCommandObjects(points[biggest_distance_index+1:-1]))

	return mc


class CommandModbus:
    """ Stores the information for a given modbus read command. """

    drop = 0
    address = 0 # type: int
    length = 0
    command = None # type: str
    write = False # type: bool
    command_chars = bytearray() 
    points = {} # type: Dict[int, Point]
    status = "" # type: str

    def __init__(
	  points: 'Dict[str, Point]',
	  command: 'str',
	  write: 'Bool',
	  drop: 'int',
    ):
        self.drop = drop # type: stir
        self.command = command # type: str
        self.write = write

        for point in points:
            self.points[point['address']] = self.point
    
    def setQuality(b: 'bool'):
        for point in self.points:
            point.quality = False

    @property
    def next_update(self) -> 'datetime':
        next_point = "no point"
        next_update = datetime.max
        if self.points is not None:
            for point in self.points.values():
                if point is not None:
                    next_update_time = p.next_update

                    if next_update_time is None:
                        continue
                    else:
                        if next_update_time < next_update:
                            next_update = next_update_time
                            next_point = p.name

        if datetime.max == next_update:
            next_update = None

        self.logger.debug(
          "next update for: %s is %s (%s)",
          self.name,
          next_update,
          next_point,
        )

        return next_update

    def getLengthRegisters(self) -> 'int':
        """ Gets the total number of registers read by this command.
        Note that there may be several registers requested by this command that
        are essentially discards. e.g. if registers 8 and 10 are required to be
        read into a variable, then this command will read 8 through 10, and
		write that data discarding register 9. In that case, this command would
		return 3 despite the fact that only 2 registers are being read. """
     
        if self.command == 'COIL' or self.command == 'DISCRETE':
            i = points[-1]['address'] - points[0]['address'] + 1
            return i

        if self.command == 'HOLDING' or self.command == 'INPUT':
            # Formula for next line = Last register - first register + length
            # of last register. 10 - 10 + 1 = 1; 11-10 + 1 = 2
            i = self.points[-1]['address'] - points[0]['address'] \
              + dataLength(points[-1]['datatype'])
            return i
        else:
            return 0

    def isContiguous(self) -> 'bool':
		""" Determines if the registers contained within this command are 
		contiguous. Knowing that the registers are contiguous is important for 
		writing data. If you needed to write to registers 4 and 6, a bulk write
		to 4,5 & 6 would be bad, since the system will probably write a 0 to 
		register 5 producing unwanted results. """
    
        nextRegister = nextRegister(self.points[0])
        for i in range(2, len(self.points)):
            if points[i]['address'] != nextRegister
                return False
            else:
                nextRegister = nextRegister(self.points[i])
        return True

    def processReply(data_bytes: 'bytearray') -> 'str':
		status = "" # type: str
		start, end, bit, pointInt = 0

		# Check and make sure packet is of minimum length
		# TODO Does minimum length depend on command type?
		if (b.len() < 10) {
			status = "Server reply is too short to process: {}".format(
			  Point.bytesToHex(b)
			)
			commandFailed();
			return status;
		}

		# Check and see if the packet contains an error.
		# If the packet is failed, the command will have 0x80 added to it
		# as per
		# http://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf
		if data_bytes[7] == -0x7f:
			commandFailed()
			# TODO incorporate the below into nice R. variables

			if data_bytes[8] == 0x01:
				status = "Illegal Function: The function code received in " \
				  + "the query is not allowed or invalid."
			
			elif data_bytes[8] == 0x02:
				status = "Illedgal Data Address: The data address received " \
				  + "in the query is not an allowable address for the slave " \
				  + "or is invalid."
			
			elif data_bytes[8] = 0x03:
				status = "Illegal Data Value: A value contained in the query " \
				  + "data field is not an allowable value for the slave or " \
				  + "is invalid."

			elif data_bytes[8] == 0x04:
				status = "Slave/Server Device Failure: The server failed " \
				  + "during execution.  An unrecoverable error occurred while" \
				  + " the slave/server was attempting to perform the " \ 
				  + " requested action"
			
			elif data_bytes[8] == 0x05:
				status = "Acknowledge: The slave/server has accepted the " \
				  + "request and is processing it, but a long duration of " \
				  + "time is required to do so.  This response is returned " \
				  + "to prevent a timeout error from occurring in the master."
			
			elif data_bytes[8] == 0x06:
				status = "Slave/Server Device Busy: The slave is engaged in " \
				  + "processing a long-duration program command. The master " \
				  + "should retransmit the message later when the slave is " \
				  + "free."
			
			elif data_bytes[8] == 0x07:
				status = "Negative Acknowledge: The slave cannot perform the " \
				  + "program function received in the query. This code is " \
				  + "returned for an unsuccessful programming request using " \
				  + "function code 13 or 14 (codes not supported by this " \
				  + "model).  The master should request diagnostic 
				  + "information from the slave. "
			
			elif data_bytes[8] == 0x08:
				status = "Memory Parity Error: The slave attempted to read " \
			      + "extended memory, but detected a parity error in memory. " \
				  + "The master can retry the request, but service may be " \
				  + "required at the slave device. "
			
			elif data_bytes[8] == 0x0a:
				status = "Gateway Problem: Gateway path(s) not available."
			
			elif data_bytes[8] == 0x0b:
				status = "Gateway Problem: The target device failed to " \
				  + "respond (the gateway generates this exception)."
			
			elif data_bytes[8] == -0x01: # -0x01 = 0xFF
				exception_length = b[9]
				exception_length = exceptionLength << 8
				exception_length += b[10]
				exeception =  bytearray(exception_length)
				exeception = b[11, exception_length + 11]
				status = "Device returned extended error: " + exception
			
			else:
				status = "Device returned an unknown error: " + b[8]
			
			return status
		
			 
		if self.command == "COIL" and self.write == True:
			""" The Force Single Coil response message is simply an echo
			(copy) of the query as shown above, but returned after
			executing the force coil command. No response is returned
			to broadcast queries from a master device (serial Modbus
			only). """

			if (not data_bytes.equals(command_chars)) {
				status = "Command 05 did not execute properly. Should 
					" have been: {} but it was: {}".format( 
					Point.bytesToHex(command_chars),
					Point.bytesToHex(data_bytes),
					)
			return
			
		if self.command == "DISCRETE" and self.write == True:
			assert False, "Cannot write to DISCRETE points"
			
		if self.command == "HOLDING" and self.write == True:
			""" The Preset Multiple Registers normal response message
			returns the slave address, function code, starting
			register reference, and the number of registers preset,
			after the register contents have been preset. Note that
			it does not echo the preset values. No response is
			returned to broadcast queries from a master device
			(serial Modbus only). 
			
			A preset multiple registers command should never be issed by
			this routine yet.
			"""
			
			c = data_bytes[0:11]
			if not c == self.command_chars:
				status = ("Command 16 did not execute properly. Should "
					+ "have been: {} but it was: {}").format(
					Point.bytesToHex(self.command_chars),
					Point.bytesToHex(data_bytes),
				)
				return status

		if self.command == "INPUT" and self.write == True:
			assert False, "Cannot write to INPUT points"

		# read command replys are dealt with below.
		if   (self.command == "COIL" 
		  or  self.command == "DISCRTE") 
		  and self.write == False:
		    for point in self.points:
				byte_index = (point['address'] - self.address) / 8 + 9
				bit_index = point['address'] % 8
				value = data_bytes[byte_index] >> bit_index & 0x01
				p.quality = True
				if value == 1:
					p.value = True
				else:
					p.value = False	

		if   (self.command == "HOLDING" 
		  or  self.command == "INPUT") 
		  and self.write == False:
            for point in self.points:
				start = (point['address'] - self.address) * 2 + 9
				end = start + dataLength(point['datatype']) * 2
				data = data_bytes[start:end]
                point.decode_datatype(
				  data=data,
				  datatype=point['datatype'],
				)

			# Deal with the case where a bit is hiding in a INPUT or
			# HOLDING register.
			if type(point) == PointDiscrete:
				match = address_regex.search(point['address'])	
			    assert match is not None, ("Point {} has an invalid " + 
				  " address for a bool-in-word").format(point.name)

				bit = match('bit')
				register = match('register')
				
				assert bit >= 0 and bit <= 15, \
					("sub-bit address is not between 0 and 15.")

				if: bit > 7
					value = (data_bytes[address] >> (bit - 8)) & 0x01
				elif: bit > 0
					value = (data_bytes	[address + 1] >> bit) & 0x01

				point.value = value

    def commandFailed(self):
	    """ Mark all points in this command as having bad quality. """
		for point in self.points:
	    	point.quality = False

    def buildCommandBytes(points: 'List[Point]') {
        """ Build the command bytes for the array of point objects.
	    Modbus TCP/IP protocol spec stolen from
	    http://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf """

	    if self.write == False:
            command_bytes = bytearray(12)
            
            if self.command == 'COIL': # COILS
                command_bytes[7] = 1;
            elif self.command == 'DISCRETE': # DISCRETES
                command_bytes[7] = 2;
            elif self.command == 'INPUT': # INPUTS
                command_bytes[7] = 3;
            elif self.command == 'HOLDING': # HOLDING
                command_bytes[7] = 4;
            else 
                assert False "Invalid command of {} given".format(
                  self.command
                )

            # Set the length of the read
            command_bytes[10] = (getLengthRegisters() >> 8) & 0xff);
            command_bytes[11] = (getLengthRegisters() & 0xff);

        else:  
			# This is a write command.
            command_chars = new byte[10];
            payload = None; # type: bytearray
            switch (command) {
            if self.command == 'COIL': # COILS are 0x reference address
                if points.len() == 1:
                    command_chars[7] = 0x05 # write single coil
                    payload = __makeCoilWritePayload__();
                elif points.len() > 1:
                	command_chars[7] = 0x15 # write multiple coils
                	payload = __makeCoilsWritePayload__();       
                
            elif self.command == 'DISCRETE':
				assert False, 'Cannot write to a DISCRETE register.'
            
            elif self.command == 'HOLDING': # 4x registers
                # TODO fix this such that it will accept several registers
                # written contiguously.
                command_chars[7] = 0x16; # 0x16 for single registers
                payload = __makeHoldingWritePayload__();
                
            elif self.command == 'INPUT':
                assert False, 'Cannot write to an INPUT register.'
            
            # Concatenate payload onto the command_chars.
            # probably should do something nicer here.
            c = bytearray(command_chars.length + payload.length)
            System.arraycopy(command_chars, 0, c, 0, command_chars.length);
            System.arraycopy(payload, 0, c, command_chars.length, payload.length);
            command_chars = c;
            }

            command_chars[0] = 0x00; // transaction identifier
            command_chars[1] = 0x00; // transaction identifier

            command_chars[2] = 0x00; // protocol identifier
            command_chars[3] = 0x00; // protocol identifier
            # The length of the packet is the total length less 6
            command_chars[4] = (byte) ((command_chars.length - 6 >> 8) & 0xff);
            command_chars[5] = (byte) ((command_chars.length - 6) & 0xff);

            command_chars[6] = drop; // unit identifier

            # We took care of byte 7 earlier.

            command_chars[8] = (byte) ((address >> 8) & 0xff);
            command_chars[9] = (byte) (address & 0xff);

		# Don't want to do multiple coil writes. For the moment only 1 coil 
		# written at a time. A well designed system should not require multiple
		# simultaneous coils to be written to at a single time to function
		# properly.

        # __makeCoilsPayload__(self) -> 'bytearray()': 
        #     """ Make boolean array for writing to the device. """
		# 	int length = getLengthRegisters();
		# 	if length % 8 == 0:
		# 		length /= 8;
		# 	else
		# 		length = length / 8 + 1;

		# 	b = bytearray(length + 2)
		# 	b[0] = (length >> 8) & 0xff
		# 	b[1] = length & 0xff;

		# 	startRegister = points[0]['address']
		# 	for (PointModbus p : points) 
		# 		if (p.getPoint().getBytes()[0] > 0) {
		# 		i = p.getRegister() - startRegister + 2;
		# 		j = i % 8;
		# 		i /= 8;
		# 		b[i] = (byte) (b[i] & (0x01 << j));
							
		# 	return b;
			

    def __makeCoilWritePayload__(self) -> 'bytearray':
		""" Build the write to a single coil (command 05) packet payload"""
		b = bytearray(2);
		if points[0].value == True:
			b[0] = 0xff # = Turn the coil on.
		else
			b[0] = 0x00 # = Turn the coil off.
		b[1] = 0x00
		return b

	# Don't want to do multiple holding register writes. For the moment only 1
	# register can be written to at a time. A well designed system should not
	# require multiple simultaneous coils to be written to at a single time to 
	# function properly.

    # make analog array for writing to the device
    # def makeHoldingWritePayload(self) {
	# 	length = getLengthRegisters();

	# 	byte[] b = new byte[length * 2 + 2];
	# 	# how many registers are we writing?
	# 	b[0] = (byte) ((length >> 8) & 0xff);
	# 	b[1] = (byte) (length & 0xff);

	# 	startRegister = points[0]['address']
	# 	for PointModbus p : points 
	# 		# i is the location in the packet that we're going to write the
	# 		# points bytes. The +1 allows for the number of registers to be
	# 		# written to be preserved
	# 		i = p.getRegister() - startRegister + 1;
	# 		i *= 2;

	# 		byte[] c = p.getPoint().getBytes();

	# 		# copy the data in.
	# 		for j = 0; j < c.length; j++
	# 		b[i + j] = c[j];
		
	# 	return b;