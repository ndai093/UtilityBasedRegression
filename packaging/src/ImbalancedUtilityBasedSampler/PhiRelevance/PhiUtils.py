import matplotlib.cbook as cbook
import numpy as np
from . import phif90_pwrapper

"""
import rdata

#/home/ndai/anaconda3/lib/python3.8/site-packages/rdata/tests/data/ImbR.rda
parsed = rdata.parser.parse_file(rdata.TESTDATA_PATH / "ImbR.rda")

converted = rdata.conversion.convert(parsed)

converted

type(converted)

#writing Pandas data frame to .csv file
df = converted['ImbR']
df.to_csv('ImbR.csv')
"""

# phiControl takes paramerters like target variable(y), method name, extreme type, coefficient, and control points (if method name is range) and calls PhiSetup and returns control points and number of rows in control points.
def phiControl(y, method="extremes", extrType="both",controlPts = [], coef=1.5):
    """
    Function to calculate Control Points and number of rows in the control points.
    :param y: list
        Target variable (continous) to calculate PhiRelevance.
    :param method: str
        Type of method used to calculate control points. Implementation supports 'extremes' and 'range' methods and default is 'extremes'.
    :param extrType: str
        If method is extremes, then need to specify extrType. It can be 'high', 'low' and 'both'. defualt is 'both'. (This is only specified for method type 'extreme').
    :param controlPts: list
        If method is 'range' then control points need to specified. the dimension of the control points can be '<n*2>' or '<n*3>'. (This is only specified for method type 'range').
    :param coef: float
        If method is 'extreme', coef is specified. coeff is the coefficient parameter in box plot statistics. default is 1.5. (This is only specified for method type 'extreme').
    :return:
        list
            Control points of size (npts * 3)
        int
            npts ( number of rows in control points).

    """
    if method == 'extremes':
        return phiExtremes(list(y), extrType, coef)
    elif method == 'range':
        return phiRange(list(y), controlPts)
    else:
        return -1, -1 


# Internal Function PhiExtremes is to calculate control points for extremes method takes variable(y), extreme type, coefficient with default control points and returns control points (type list) and number of rows in control points (type integer).
def phiExtremes(y, extrType, coef=1.5):
    npts =0
    controlPts = []

    # calculates all statistics of target continous variable with given coef, and return in the form of array of map
    extr = cbook.boxplot_stats(y,whis=coef)
    extr= extr[0]

    r=[0,0]
    r[0] = min(y)
    r[1] = max(y)

    # if extreme type is (both or low) and checking any fliers values less then lower whisker value
    if(extrType in ["both","low"] and len([i for i in extr['fliers'] if i < extr['whislo']])>0):
        controlPts.append(extr['whislo'])
        controlPts.append(1)
        controlPts.append(0)
        npts+=1
    else:
        controlPts.append(r[0])
        controlPts.append(0)
        controlPts.append(0)
        npts+=1

    # if median not equal to min of continous variable
    if(extr['med'] != r[0]):
        controlPts.append(extr['med'])
        controlPts.append(0)
        controlPts.append(0)
        npts += 1

    # if extreme type is (both or high) and checking any fliers values greater then higher whisker value
    if (extrType in ["both", "high"] and len([i for i in extr['fliers'] if i > extr['whishi']]) > 0):
        controlPts.append(extr['whishi'])
        controlPts.append(1)
        controlPts.append(0)
        npts += 1
    else:
        controlPts.append(r[1])
        controlPts.append(0)
        controlPts.append(0)
        npts += 1

    return controlPts, npts


# Internal Function phiRange is to calculate control points for range method takes variable(y), control points and default extrType and coef and returns control points and number of rows in control points.
def phiRange(y, controlPts = []):

    # if controlPts length(rows) is less than or equal to 0, return -1,-1
    if(len(controlPts)<=0):
        print("The controlPts should not be empty")
        return -1,-1

    # if controlPts columns are greater than 3 or  less than 2, return -1,-1
    elif(len(controlPts[0])>3 or len(controlPts[0])<2):
        print("The controlPts must must be given as a matrix in the form: \n" + "< x, y, m > or, alternatively, < x, y >")
        return  -1,-1

    npts = len(controlPts)

    # getting all first columns in control points
    y = [i[0] for i in controlPts]

    # getting all second columns in control points
    p = [i[1] for i in controlPts]

    # creating 2 temporary list for y and p by removing first element for first temp(y1,p1) list and removing last element for second temp list (y2,p2).
    y1,y2 = y[1:],y[:-1]
    p1,p2 = p[1:],p[:-1]

    dy = []
    # calculating difference of y1 and y2 and storing in dy list
    # y should be continous and increasing
    for i in range(len(y1)):
        if(y1[i]-y2[i] <= 0):
            print('y must be *strictly* increasing (non - NA)')
            return -1,-1
        dy.append(y1[i]-y2[i])

    dp = []
    # calculating difference of p1 and p2 and storing in dp list
    # p should be either 0 or 1
    for i in range(len(p1)):
        if(p1[i]>1 or p1[i] <0):
            print("phi relevance function values only in [0,1]")
        dp.append(p1[i]-p2[i])

    # sorting based on first column.
    controlPts = sorted(controlPts, key=lambda x: x[0])

    # if control points is 2D, it calculates for 3rd column
    if(len(controlPts[0]) == 2):
        sx=[]
        for i in range(len(dy)):
            sx.append(dp[i]/dy[i])

        sx1,sx2 = sx[1:],sx[:-1]
        dsx = []
        dsx.append(0)
        for i in range(len(sx1)):
            dsx.append((sx1[i]+sx2[i])/2)
        dsx.append(0)

        for i in range(len(controlPts)):
            controlPts[i].append(dsx[i])

    npts = len(controlPts)

    cPts = []
    for i in controlPts:
        cPts.extend(i)
    controlPts = cPts

    return controlPts, npts


# phi takes target continous variable, control points generted by phiControl function, number of rows in control points, and method name and returns yphi, ydphi, yddphi (phi values for target varaibles, first derivative and second derivative)
def phi(y,controlParams,npts,method):
    """

    :param y: list
        Target variable (continous) to calculate PhiRelevance.
    :param controlParams: list
        controlPoints generted using phiControl function.
    :param npts: int
        number of rows in control points.
    :param method: str
        Type of method used in calculation of control points with phiControl.
    :return:
        list
            yphi (phi values for target varaibles)
        list
            ydphi (first derivative phi values for target varaibles)
        list
            yddphi (second derivative phi values for target varaibles)
    """
    n=len(y)
    if(method == 'extremes'):
        meth = 0
    else:
        meth = 1
    lparms = len(controlParams)
    phiParms = controlParams
    yPhi = np.reshape([0.0]*n,(-1,1))
    ydPhi = np.reshape([0.0]*n,(-1,1))
    yddPhi = np.reshape([0.0]*n,(-1,1))

    # Wrapper of fortran code calling rtophi function implemeted in fortran
    # print(phif90_pwrapper.rtophi.__doc__)
    phif90_pwrapper.rtophi(y, meth, npts, phiParms, yPhi, ydPhi, yddPhi,[n,lparms])

    yPhi = [i[0] for i in yPhi]
    ydPhi = [i[0] for i in ydPhi]
    yddPhi = [i[0] for i in yddPhi]

    return yPhi,ydPhi,yddPhi