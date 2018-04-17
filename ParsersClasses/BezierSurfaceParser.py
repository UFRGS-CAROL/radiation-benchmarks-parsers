
from Parser import Parser
import re
#HEADER: openclBezierSurface "-i %d -g %d -a %.2f -t %d -n %d"
#p: [%d, %d]; X r: %f, e: %f ; Y r: %f, e: %f ; Z r: %f, e: %f"

class BezierSurfaceParser(Parser):

	#__errorLimits = [0.0, 2.0, 5.0]
	#_machine= "" #As string
	#_benchmark = None
	#_header = ""
	#_hasThirdDimention = False

#***************************************************
# Error Line parser Method
#***************************************************
    def parseErrMethod(self, errString):
        # print errString

		try:	
			m = re.match(".*ERR.*p: \[(\d+)\, (\d+)\].*X r\: (\d+\.\d+).* e\: (\d+\.\d+).*Y r\: (\d+\.\d+).*e\: (\d+\.\d+).*Z r\: (\d+\.\d+).*e\: (\d+\.\d+).*",errString)

		    if m:
				px = int(m.group(1))
				py = int(m.group(2))
			
				xr = float(m.group(3))
				xe = float(m.group(4))	

				yr = float(m.group(5))
				ye = float(m.group(6))	

				zr = float(m.group(7))
				ze = float(m.group(8))	
			    return [px,py,xr,xe,yr,ye,zr,ze]
			else:
				print("Error Parsing Error Line")
				return None			
		
		except ValueError:
			return None		
#********************************************
# In this function the real parsing happends
#     All error type calculation 
#********************************************
    def _relativeErrorParser(self, errList):
        if len(errList) <= 0:
            return

        for i in errList:
            print i


#*********************************************
# Header parser Method 
# 	header is a string containing header-info 
#*********************************************
    def setSize(self, header):
        ##HEADER -i 5 -g 5 -a 1.00 -t 4 -n 2500
        m = re.match(".*\-i (\d+).*\-g (\d+).*\-a (\S+).*\-t (\d+).*\-n (\d+).*", header)
        if m:
            self._i = m.group(1)	# Work-items
            self._g = m.group(2)	# Work-group
            self._a = float(m.group(3)) # %CPU Execution
            self._t = m.group(4)	# Threads
            self._n = m.group(5)	# Outsize Resolution
            self._size = str(self._i) + "_" + str(self._g) + "_" + str(self._a) + "_" + str(self._t) + "_" + str(self._n)
		else:
			print("Error Reading Header Line")	
	        self._size = None


    """
    LEGACY METHODS SECTION
    """
    """
    legacy method
    """
    # def __init__(self, **kwargs):
    #     Parser.__init__(self, **kwargs)

    """
    legacy method
    """
    # def buildImageMethod(self):
    #     # type: (integer) -> boolean
    #     return False
