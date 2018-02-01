# This file is part of the udkm1Dsimpy module.
#
# udkm1Dsimpy is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2017 Daniel Schick

import numpy as np
from inspect import isfunction
from sympy import integrate, Symbol
from sympy.utilities.lambdify import lambdify
import numericalunits as u
u.reset_units('SI')

class unitCell(object):
    """unitCell

    The unitCell class hold different structural properties of real physical
    unit cells and also an array of atoms at different postions in the unit
    cell.

    ID (str)                        : ID of the unit cell
    name (str)                      : name of the unit cell
    atoms (list[atom, @lambda])     : list of atoms and funtion handle for
                                    strain dependent displacement
    numAtoms (int)                  : number of atoms in unit cell
    aAxis (float)                   : in-plane a-axis [m]
    bAxis (float)                   : in-plane b-axis [m]
    cAxis (float)                   : out-of-plane c-axis [m]
    area  (float)                   : area of epitaxial unit cells
                                      need for normation for correct intensities) [m^2]
    volume (float)                  : volume of unit cell [m^3]
    mass (float)                    : mass of unit cell normalized to an area of 1 Ang^2 [kg]
    density (float)                 : density of the unitCell [kg/m^3]
    debWalFac (float)               : Debye Waller factor <u>^2 [m^2]
    soundVel (float)                : sound velocity in the unit cell [m/s]
    springConst (ndarray[float])    : spring constant of the unit cell [kg/s^2] and higher orders
    phononDamping (float)           : damping constant of phonon propagation [kg/s]
    optPenDepth (float)             : penetration depth for pump always for 1st subsystem
                                    light in the unit cell [m]
    optRefIndex (ndarray[float])    : optical refractive index - real and imagenary part $n + i\kappa$
    optRefIndexPerStrain (ndarray[float])   :
            optical refractive index change per strain -
            real and imagenary part %\frac{d n}{d \eta} + i\frac{d \kappa}{d \eta}$
    thermCond (list[@lambda])               :
            list of HANDLES T-dependent thermal conductivity [W/(m K)]
    linThermExp (list[@lambda])             :
            list of HANDLES T-dependent linear thermal expansion coefficient (relative)
    intLinThermExp (list[@lambda])          :
            list of HANDLES T-dependent integrated linear thermal expansion coefficient
    heatCapacity (list[@lambda])            :
            list of HANDLES T-dependent heat capacity function [J/(kg K)]
    intHeatCapacity (list[@lambda])         :
            list of HANDLES T-dependent integrated heat capacity function
    subSystemCoupling (list[@lambda])       :
            list of HANDLES of coupling functions of different subsystems [W/m^3]
    numSubSystems (int)                     :
            number of subsystems for heat and phonons (electrons, lattice, spins, ...)
    """

    def __init__(self, ID, name, cAxis, **kwargs):
        # % initialize input parser and define defaults and validators
        # p = inputParser;
        # p.addRequired('ID'                      , @ischar);
        # p.addRequired('name'                    , @ischar);
        # p.addRequired('cAxis'                   , @isnumeric);
        # p.addParamValue('aAxis'                 , cAxis , @isnumeric);
        # p.addParamValue('bAxis'                 , cAxis , @isnumeric);
        # p.addParamValue('debWalFac'             , 0     , @isnumeric);
        # p.addParamValue('soundVel'              , 0     , @isnumeric);
        # p.addParamValue('phononDamping'         , 0     , @isnumeric);
        # p.addParamValue('optPenDepth'           , 0     , @isnumeric);
        # p.addParamValue('optRefIndex'           , [0,0] , @(x) (isnumeric(x) && numel(x) == 2));
        # p.addParamValue('optRefIndexPerStrain'  , [0,0] , @(x) (isnumeric(x) && numel(x) == 2));
        # p.addParamValue('thermCond'             , 0     , @(x)(isnumeric(x) || isa(x,'function_handle') || ischar(x) || iscell(x)));
        # p.addParamValue('linThermExp'           , 0     , @(x)(isnumeric(x) || isa(x,'function_handle') || ischar(x) || iscell(x)));
        # p.addParamValue('heatCapacity'          , 0     , @(x)(isnumeric(x) || isa(x,'function_handle') || ischar(x) || iscell(x)));
        # p.addParamValue('subSystemCoupling'     , 0     , @(x)(isnumeric(x) || isa(x,'function_handle') || ischar(x) || iscell(x)));
        # % parse the input
        # p.parse(ID,name,cAxis,varargin{:});
        # % assign parser results to object properties
        self.ID = ID
        self.name = name
        self.cAxis = cAxis
        self.aAxis = kwargs.get('aAxis', self.cAxis)
        self.bAxis = kwargs.get('bAxis', self.aAxis)
        self.atoms          = []
        self.numAtoms       = 0
        self.mass           = 0
        self.density        = 0
        self.springConst    = np.array([0])
        self.debWalFac               = kwargs.get('debWalFac', 0)
        self.soundVel                = kwargs.get('soundVel', 0)
        self.phononDamping           = kwargs.get('phononDamping', 0)
        self.optPenDepth             = kwargs.get('optPenDepth', 0)
        self.optRefIndex             = kwargs.get('optRefIndex', 0)
        self.optRefIndexPerStrain    = kwargs.get('optRefIndexPerStrain', 0)
        self.heatCapacity, self.heatCapacityStr \
                                     = self.checkCellArrayInput(kwargs.get('heatCapacity', 0))
        self.thermCond, self.thermCondStr \
                                     = self.checkCellArrayInput(kwargs.get('thermCond', 0))
        self.linThermExp, self.linThermExpStr \
                                     = self.checkCellArrayInput(kwargs.get('linThermExp', 0))
        self.subSystemCoupling, self.subSystemCouplingStr \
                                     = self.checkCellArrayInput(kwargs.get('subSystemCoupling', 0))

        if len(self.heatCapacity) == len(self.thermCond) \
            and len(self.heatCapacity) == len(self.linThermExp) \
            and len(self.heatCapacity) == len(self.subSystemCoupling):
            self.numSubSystems = len(self.heatCapacity)
        else:
            raise ValueError('Heat capacity, thermal conductivity, linear'
                'thermal expansion and subsystem coupling have not the same number of elements!')

        self.area           = self.aAxis * self.bAxis
        self.volume         = self.area * self.cAxis

    def __str__(self):
        """String representation of this class

        """
        classStr  = 'Unit Cell with the following properties\n'
        classStr += 'ID                     : {:s}\n'.format(self.ID)
        classStr += 'name                   : {:s}\n'.format(self.name)
        classStr += 'a-axis                 : {:3.2f} Å\n'.format(self.aAxis/u.angstrom)
        classStr += 'b-axis                 : {:3.2f} Å\n'.format(self.bAxis/u.angstrom)
        classStr += 'c-axis                 : {:3.2f} Å\n'.format(self.cAxis/u.angstrom)
        classStr += 'area                   : {:3.2f} Å²\n'.format(self.area/u.angstrom**2)
        classStr += 'volume                 : {:3.2f} Å³\n'.format(self.volume/u.angstrom**3)
        classStr += 'mass                   : {:3.2e} kg\n'.format(self.mass/u.kg)
        classStr += 'density                : {:3.2e} kg/m³\n'.format(self.density/(u.kg/u.m**3))
        classStr += 'Debye Waller Factor    : {:3.2f} m²\n'.format(self.debWalFac/u.m**2)
        classStr += 'sound velocity         : {:3.2f} nm/ps\n'.format(self.soundVel/(u.nm/u.ps))
        classStr += 'spring constant        : {:s} kg/s²\n'.format(np.array_str(self.springConst/(u.kg/u.s**2)))
        classStr += 'phonon damping         : {:3.2f} kg/s\n'.format(self.phononDamping/(u.kg/u.s))
        classStr += 'opt. pen. depth        : {:3.2f} nm\n'.format(self.optPenDepth/u.nm)
        classStr += 'opt. refractive index  : {:3.2f}\n'.format(self.optRefIndex)
        classStr += 'opt. ref. index/strain : {:3.2f}\n'.format(self.optRefIndexPerStrain)
        classStr += 'thermal conduct. [W/m K]       :\n'
        for func in self.thermCondStr:
            classStr += '\t\t\t {:s}\n'.format(func)
        classStr += 'linear thermal expansion [1/K] :\n'
        for func in self.linThermExpStr:
            classStr += '\t\t\t {:s}\n'.format(func)
        classStr += 'heat capacity [J/kg K]         :\n'
        for func in self.heatCapacityStr:
            classStr += '\t\t\t {:s}\n'.format(func)
        classStr += 'subsystem coupling [W/m^3]     :\n'
        for func in self.subSystemCouplingStr:
            classStr += '\t\t\t {:s}\n'.format(func)
        # display the constituents
        classStr += str(self.numAtoms) + ' Constituents:\n'
        for i in range(self.numAtoms):
            classStr += '{:s} \n {:0.2f} \t {:s}\n'.format(self.atoms[i][0].name, self.atoms[i][1](0), self.atoms[i][2])

        return(classStr)

    def visualize(self, **kwargs):
        import matplotlib.pyplot as plt
        import matplotlib.cm as cmx

        strains = kwargs.get('strains', 0)
        if not isinstance(strains, np.ndarray):
            strains = np.array([strains])

        colors          = [cmx.Dark2(x) for x in np.linspace(0, 1.5, self.numAtoms)]
        atomIDs         = self.getAtomIDs()

        for strain in strains:
            plt.figure()
            atomsPlotted    = np.zeros_like(atomIDs)
            for j in range(self.numAtoms):
                if not atomsPlotted[atomIDs.index(self.atoms[j][0].ID)]:
                    label = self.atoms[j][0].ID
                    atomsPlotted[atomIDs.index(self.atoms[j][0].ID)] = True
                else:
                    label = '_nolegend_'

                l = plt.plot(1+j,self.atoms[j][1](strain), 'o', MarkerSize=10,
                    markeredgecolor=[0, 0, 0], markerfaceColor=colors[atomIDs.index(self.atoms[j][0].ID)],
                    label=label)

            plt.axis([0.1, self.numAtoms+0.9, -0.1, (1.1+np.max(strains))])
            plt.grid(True)

            plt.title('Strain: {:0.2f}%'.format(strain));
            plt.ylabel('relative Position');
            plt.xlabel('# Atoms');
            plt.legend()
            plt.show()

    def getPropertyStruct(self, **kwargs):
        """getParameterStruct

        Returns a struct with all parameters. objects or cell arrays and
        objects are converted to strings. if a type is given, only these
        properties are returned.
        """
        # initialize input parser and define defaults and validators
        types = ['all', 'heat', 'phonon', 'XRD', 'optical']
        propertiesByTypes = {
                'heat'     : ['cAxis', 'area', 'volume', 'optPenDepth', 'thermCondStr', 'heatCapacityStr', 'intHeatCapacityStr', 'subSystemCouplingStr', 'numSubSystems'],
                'phonon'   : ['numSubSystems', 'intLinThermExpStr', 'cAxis', 'mass', 'springConst', 'phononDamping'],
                'XRD'      : ['numAtoms', 'atoms', 'area', 'debWalFac', 'cAxis'],
                'optical'  : ['cAxis', 'optPenDepth', 'optRefIndex', 'optRefIndexPerStrain'],
                }

        types = kwargs.get('types')
        attrs = vars(self)
        # define the property names by the given type
        if types == 'all':
            S = attrs
        else:
            S = dict((key, value) for key, value in attrs.items() if key in propertiesByTypes[types])

        return S

    def checkCellArrayInput(self, inputs):
        """ checkCellArrayInput

        Checks the input for inputs which are cell arrays of function
        handles, such as the heat capacity which is a cell array of N
        function handles.
        """
        output      = []
        outputStrs  = []
        # if the input is not a list, we convert it to one
        if not isinstance(inputs, list):
            inputs = [inputs]
        # traverse each list element and convert it to a function handle
        for input in inputs:
            if isfunction(input):
                raise ValueError('Please use string representation of function!')
                output.append(input)
                outputStrs.append('no str representation available')
            elif isinstance(input, str):
                try:
                    output.append(eval(input))
                    outputStrs.append(input)
                except Exception as e:
                    print('String input for unit cell property ' + input + ' \
                        cannot be converted to function handle!')
                    print(e)
            elif isinstance(input, (int, float)):
                output.append(eval('lambda T: {:f}'.format(input)))
                outputStrs.append('lambda T: {:f}'.format(input))
            else:
                raise ValueError('Unit cell property input has to be a single or'
                'cell array of numerics, function handles or strings which can be'
                'converted into a function handle!')

        return(output, outputStrs)

    @property
    def intHeatCapacity(self):
        """get intHeatCapacity

        Returns the anti-derrivative of the temperature-dependent heat
        $c(T)$ capacity function. If the _intHeatCapacity_ property is
        not set, the symbolic integration is performed.
        """

        if hasattr(self, '_intHeatCapacity') and isinstance(self._intHeatCapacity, list):
            h = self._intHeatCapacity
        else:
            self._intHeatCapacity = []
            self.intHeatCapacityStr = []
            try:
                T = Symbol('T')
                for i, hcs in enumerate(self.heatCapacityStr):
                    integral = integrate(hcs.split(':')[1], T)
                    self._intHeatCapacity.append(lambdify(T, integral))
                    self.intHeatCapacityStr.append('lambda T : ' + str(integral))

            except Exception as e:
                print('The sympy integration did not work. You can set the'
                'analytical anti-derivative of the heat capacity'
                'of your unit cells as lambda function of the temperature'
                'T by typing UC.intHeatCapacity = lambda T: c(T)'
                'where UC is the name of the unit cell object.')
                print(e)

        return(self._intHeatCapacity)

    @intHeatCapacity.setter
    def intHeatCapacity(self, intHeatCapacity):
        """set intHeatCapacity

        Set the integrated heat capacity manually when no Smybolic Math
        Toolbox is installed.
        """
        self._intHeatCapacity, self.intHeatCapacityStr = self.checkCellArrayInput(intHeatCapacity)

    @property
    def intLinThermExp(self):
        """get intLinThermExp

        Returns the anti-derrivative of theintegrated temperature-dependent
        linear thermal expansion function. If the __intLinThermExp__
        property is not set, the symbolic integration is performed.
        """

        if hasattr(self, '_intLinThermExp') and isinstance(self._intLinThermExp, list):
            h = self._intLinThermExp
        else:
            self._intLinThermExp = []
            self.intLinThermExpStr = []
            try:
                T = Symbol('T')
                for i, ltes in enumerate(self.linThermExpStr):
                    integral = integrate(ltes.split(':')[1], T)
                    self._intLinThermExp.append(lambdify(T, integral))
                    self.intLinThermExpStr.append('lambda T : ' + str(integral))

            except Exception as e:
                print('The sympy integration did not work. You can set the'
                'the analytical anti-derivative of the heat capacity'
                'of your unit cells as lambda function of the temperature'
                'T by typing UC.intHeatCapacity = lambda T: c(T)'
                'where UC is the name of the unit cell object.')
                print(e)

        return(self._intLinThermExp)

    @intLinThermExp.setter
    def intLinThermExp(self, intLinThermExp):
        """set intLinThermExp

        Set the integrated linear thermal expansion coefficient manually
        when no Smybolic Math Toolbox is installed.
        """
        self._intLinThermExp, self.intLinThermExpStr = self.checkCellArrayInput(intLinThermExp)

    def addAtom(self, atom, position):
        """ addAtom
        Adds an atomBase/atomMixed at a relative position of the unit
        cell.
        """

        positionStr = ''
        # test the input type of the position
        if isfunction(position):
            raise ValueError('Please use string representation of function!')
            pass
        elif isinstance(position, str):
            try:
                positionStr = position
                position = eval(position)
            except Exception as e:
                print('String input for unit cell property ' + position + ' \
                    cannot be converted to function handle!')
                print(e)
        elif isinstance(position, (int, float)):
            positionStr = 'lambda strain: {:e}*(strain+1)'.format(position)
            position = eval(positionStr);
        else:
            raise ValueError('Atom position input has to be a scalar, or string'
                    'which can be converted into a lambda function!')

        # add the atom at the end of the array
        self.atoms.append([atom, position, positionStr])
        # increase the number of atoms
        self.numAtoms = self.numAtoms + 1
        # Update the mass, density and spring constant of the unit cell
        # automatically:
        #
        # $$ \kappa = m \cdot (v_s / c)^2 $$

        self.mass = 0;
        for i  in range(self.numAtoms):
            self.mass = self.mass + self.atoms[i][0].mass

        self.density     = self.mass / self.volume
        # set mass per unit area (do not know if necessary)
        self.mass        = self.mass * 1*u.angstrom**2 / self.area
        self.calcSpringConst()

    def addMultipleAtoms(self, atom, position, Nb):
        """addMultipleAtoms

        Adds multiple atomBase/atomMixed at a relative position of the unit
        cell.
        """
        for i in range(Nb):
           self.addAtom(atom,position)

    def calcSpringConst(self):
        """ calcSpringConst

        Calculates the spring constant of the unit cell from the mass,
        sound velocity and c-axis

        $$ k = m \, \left(\frac{v}{c}\right)^2 $$
        """
        self.springConst[0] = self.mass * (self.soundVel/self.cAxis)**2

    def getAcousticImpedance(self):
        """getAcousticImpedance
        """
        Z = np.sqrt(self.springConst[0] * self.mass/self.area**2)
        return(Z)

    @property
    def soundVel(self):
        return self._soundVel

    @soundVel.setter
    def soundVel(self, soundVel):
        """set.soundVel
        If the sound velocity is set, the spring constant is
        (re)calculated.
        """
        self._soundVel = soundVel
        self.calcSpringConst()

    def setHOspringConstants(self, HO):
        """setHOspringConstants

        Set the higher orders of the spring constant for anharmonic
        phonon simulations.
        """
      
        # reset old higher order spring constants
        self.springConst = np.delete(self.springConst,
                            np.r_[1:len(self.springConst)])
        self.springConst = np.hstack((self.springConst, HO))

    def getAtomIDs(self):
        """getAtomIDs

        Returns a cell array of all atom IDs in the unit cell.
        """

        IDs = []
        for i in range(self.numAtoms):
            if not self.atoms[i][0].ID in IDs:
                IDs.append(self.atoms[i][0].ID)

        return IDs

    def getAtomPositions(self, *args):
        """getAtomPositions

        Returns a vector of all relative postion of the atoms in the unit
        cell.
        """

        if args:
            strain = args
        else:
            strain = 0
        strain = np.array(strain)
        res = np.zeros([self.numAtoms])
        for i, atom in enumerate(self.atoms):
            res[i] = atom[1](strain)

        return res
