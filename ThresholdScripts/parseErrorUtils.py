#!/usr/bin/env python

import re

# Returns an error item in dict form: {"positions" : listPosition, "values" : listValues}
# Returns None if it is not possible to parse
def parseErrLavaMD(errString, header):
        box = None
        m = re.match(".*boxes[\:-](\d+).*", header)
        if m:
        	try:
        		box = int(m.group(1))
        	except:
        		box = None
        m = re.match(".*box[\:-](\d+).*", header)
        if m:
        	try:
        		box = int(m.group(1))
        	except:
        		box = None
	if box is None:
		print ("box is None!!!\nerrString: ",errString)
		print("header: ",header)
		return None

	try:
		##ERR p: [357361], ea: 4, v_r: 1.5453305664062500e+03, v_e: 1.5455440673828125e+03, x_r: 9.4729260253906250e+02, x_e: 9.4630560302734375e+02, y_r: -8.0158099365234375e+02, y_e: -8.0218914794921875e+02, z_r: 9.8227819824218750e+02, z_e: 9.8161871337890625e+02
		m = re.match(".*ERR.*\[(\d+)\].*v_r\: ([0-9e\+\-\.]+).*v_e\: ([0-9e\+\-\.]+).*x_r\: ([0-9e\+\-\.]+).*x_e\: ([0-9e\+\-\.]+).*y_r\: ([0-9e\+\-\.]+).*y_e\: ([0-9e\+\-\.]+).*z_r\: ([0-9e\+\-\.]+).*z_e\: ([0-9e\+\-\.]+)", errString)
		if m:
			pos = int(m.group(1))
			boxSquare = box * box
			posZ = int( pos / boxSquare )
			posY = int( (pos-(posZ*boxSquare)) / box )
			posX = pos-(posZ*boxSquare)-(posY*box)

			vr = float(m.group(2))
			ve = float(m.group(3))
			xr = float(m.group(4))
			xe = float(m.group(5))
			yr = float(m.group(6))
			ye = float(m.group(7))
			zr = float(m.group(8))
			ze = float(m.group(9))
                        positions = [ ["x",posX], ["y",posY], ["z",posZ] ]
                        values = [ ["v", vr, ve], ["x", xr, xe], ["y", yr, ye], ["z", zr, ze] ]
                        return {"position":positions, "values":values}
			#return [posX, posY, posZ, vr, ve, xr, xe, yr, ye, zr, ze]
		else:
			return None
	except ValueError:
		return None

# Returns an error item in dict form: {"positions" : listPosition, "values" : listValues}
# Returns None if it is not possible to parse
# Works for GEMM and LUD
def parseErrMethod1(errString, header):
	try:
                #lud:
                #ERR  p: [3708, 3131], r: 1.1220343410968781e-02, e: 1.1220589280128479e-02
                #dgemm:
		#ERR stream: 0, p: [0, 0], r: 3.0815771484375000e+02, e: 0.0000000000000000e+00
		m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\: ([0-9e\+\-\.]+).*e\: ([0-9e\+\-\.]+)", errString)
		if m:
			posX = int(m.group(1))
			posY = int(m.group(2))
			read = float(m.group(3))
			expected = float(m.group(4))
                        positions = [ ["x",posX], ["y",posY] ]
                        values = [ ["v", read, expected] ]
                        return {"position":positions, "values":values}
			#return [posX, posY, read, expected]
		else:
			return None
	except ValueError:
		return None

# Returns an error item in dict form: {"positions" : listPosition, "values" : listValues}
# Returns None if it is not possible to parse
# Works for Hotspot OpenCL and CUDA
def parseErrMethod2(errString, header):
	try:
		m = re.match(".*ERR.*.*r\:([0-9e\+\-\.nan]+).*e\:([0-9e\+\-\.]+).*\[(\d+),(\d+)\]", errString)
		#OCL -> ERR r:293.943054 e:293.943024 [165,154]
		if m: 
			posX=int(m.group(3))
			posY=int(m.group(4))
			read=m.group(1)
			expected=float(m.group(2))
			if re.match(".*nan.*",read):
                            positions = [ ["x",posX], ["y",posY] ]
                            values = [ ["v", expected*2, expected] ]
                            return {"position":positions, "values":values}
	                    #return [posX, posY, expected*2, expected]
			else:
			    read = float(read)
                            positions = [ ["x",posX], ["y",posY] ]
                            values = [ ["v", read, expected] ]
                            return {"position":positions, "values":values}
			    #return [posX, posY, read, expected]

		m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\: ([0-9e\+\-\.nan]+).*e\: ([0-9e\+\-\.]+)", errString)
		#CUDA -> ERR stream: 0, p: [0, 0], r: 3.0815771484375000e+02, e: 0.0000000000000000e+00
		if m: 
			posX=int(m.group(1))
			posY=int(m.group(2))
			read=m.group(3)
			expected=float(m.group(4))
			if re.match(".*nan.*",read):
                            positions = [ ["x",posX], ["y",posY] ]
                            values = [ ["v", expected*2, expected] ]
                            return {"position":positions, "values":values}
			    #return [posX, posY, expected*2, expected]
			else:
			    read = float(read)
                            positions = [ ["x",posX], ["y",posY] ]
                            values = [ ["v", read, expected] ]
                            return {"position":positions, "values":values}
			    #return [posX, posY, read, expected]
		return None
	except:
		return None

def getParserFunction(benchmark):
	isHotspot = re.search("hotspot",benchmark,flags=re.IGNORECASE)
	isGEMM = re.search("GEMM",benchmark,flags=re.IGNORECASE)
	isLavaMD = re.search("lavamd",benchmark,flags=re.IGNORECASE)
	isCLAMR = re.search("clamr",benchmark,flags=re.IGNORECASE)
	isLUD = re.search("lud",benchmark,flags=re.IGNORECASE)
	errorsParsed = []
        parseFunc = None
	if isGEMM or isLUD:
            parseFunc = parseErrMethod1
        elif isHotspot:
            parseFunc = parseErrMethod2
	elif isLavaMD:
            parseFunc = parseErrLavaMD

        return parseFunc


def parseErrors(errList, benchmark, header):
        parserFunc = getParserFunction(benchmark)
        if parserFunc is None:
            return None

	errorsParsed = []
	# Get error details from log string
	for errString in errList:
		err = parserFunc(errString, header)
		if err is not None:
			errorsParsed.append(err)
        return errorsParsed

def hasParser(benchmark):
    if getParserFunction(benchmark) is None:
        return False
    else:
        return True
        


