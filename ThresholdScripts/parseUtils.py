#!/usr/bin/env python

import collections

#benchmarks dict => (bechmarkname_machinename : list of SDC item)
#SDC item => [logfile name, header, sdc iteration, iteration total amount error, iteration accumulated error, list of errors ]
#list of errors => list of strings with all the error detail print in lines using #ERR


# errList => [ {"positions" : listPosition, "values" : listValues} ]
#
# position item from listPosition => ["name", value]
# example of listPosition:
#   positionsExample = [ ["x",5], ["y",10], ["z",0] ]
#
# value item from listValues => ["name", read, expected]
# example of listValues:
#   valuesExample = [ ["force", 10, 10], ["energy", 10, 12], ["velocity", 1, 9] ]
#
# example of errList:
#  errList = [ {"position" : positionsExample, "values" : valuesExample} ]
#
# A complete example below shows two errors being inserted into errList:
#    errList = list()
#
#    positionsExample = [ ["x",5], ["y",10], ["z",0] ]
#    valuesExample = [ ["force", 10, 10], ["energy", 10, 11], ["velocity", 1, 9] ]
#    errItem = {"position" : positionsExample, "values" : valuesExample}
#
#    errList.append(errItem)
#
#    positionsExample2 = [ ["x",5], ["y",0], ["z",40] ]
#    valuesExample2 = [ ["force", 10, 9.5], ["energy", 20, 21], ["velocity", 5, 5] ]
#    errItem2 = {"position" : positionsExample2, "values" : valuesExample2}
#
#    errList.append(errItem2)


# Return a list as follows: 
# [
#   highest relative error,
#   lowest relative error,
#   average relative error,
#   number of errors with relative errors lower than the limit sepecified in the parameter errLimit, 
#   list of errors filtered by the errLimit (a list with only the errors higher than errLimit)
# ]
def relativeErrorParser(errList, errLimit):
	relErr = []
	relErrLowerLimit = 0
	errListFiltered = []
	for errItem in errList:
            relErrorSum = 0
            for val in errItem["values"]:
                #name = val[0]
		read = float(val[1])
		expected = float(val[2])
		absoluteErr = float(abs(expected - read))
                # Only compare relative errors with numbers higher than zero
		if (abs(read) > 1e-6) and (abs(expected) > 1e-6):
                    relError = ( absoluteErr / abs(expected) ) * 100
                    relErrorSum += relError
	    relErr.append( relErrorSum )
	    if relErrorSum < errLimit:
		relErrLowerLimit += 1
	    else:
		errListFiltered.append(errItem)

	if len(relErr) > 0:
		maxRelErr = max(relErr)
		minRelErr = min(relErr)
		avgRelErr = sum(relErr)/float(len(relErr))
		return[maxRelErr,minRelErr,avgRelErr,relErrLowerLimit,errListFiltered]
	else:
		return[None,None,None,relErrLowerLimit,errListFiltered]

# Return how many zeros the output and gold values have
def countZerosReadExpected(errList):
    zeroGold = 0
    zeroOut = 0
    for errItem in errList:
        relErrorSum = 0
        for val in errItem["values"]:
            #name = val[0]
            read = float(val[1])
            expected = float(val[2])
	    if abs(read) < 1e-6:
	    	zeroOut += 1
	    if abs(expected) < 1e-6:
	    	zeroGold += 1
    return [zeroOut, zeroGold]


# Return how many dimensions have multiple error.
# Used to compute the error locality if there is more than one error, for example: 
# if there is 0 dimensions with multiple error: locality is random.
# if there is 1 dimension with multiple error: locality is line.
# if there is 2 dimensions with multiple error: locality is square.
# if there is 3 dimensions with multiple error: locality is cubic.
# if there is 4 dimensions with multiple error: locality is hypercube???.
#
# If there is ONLY ONE ERROR, the locality should be SINGLE
def localityMultiDimensional(errList):
        if errList is None:
            return None
        if len(errList) == 0:
            return None
        positions = [x["position"] for x in errList]
        numDimensions = len(positions[0])
        dimensionsMultipleErrors = 0
        for i in range(0,numDimensions):
            AllPositionsThisDimension = [x[i][1] for x in positions]
            counterPositions = collections.Counter(AllPositionsThisDimension)
            if (any(x>1 for x in counterPositions.values())): # Check if any value is in the list more than one time
                dimensionsMultipleErrors += 1
        return dimensionsMultipleErrors



###errList = list()
###
###positionsExample = [ ["x",5], ["y",10], ["z",0] ]
###valuesExample = [ ["force", 10, 10], ["energy", 10, 11], ["velocity", 1, 9] ]
###errItem = {"position" : positionsExample, "values" : valuesExample}
###errList.append(errItem)
###positionsExample2 = [ ["x",5], ["y",0], ["z",40] ]
###valuesExample2 = [ ["force", 10, 9.5], ["energy", 20, 21], ["velocity", 5, 5] ]
###errItem2 = {"position" : positionsExample2, "values" : valuesExample2}
###
###errList.append(errItem2)
###
###print "locality: ",localityMultiDimensional(errList)
###sys.exit(0)
###
###errLimit = 2
###print errList
###print "result:"
###print relativeErrorParser(errList, errLimit)
