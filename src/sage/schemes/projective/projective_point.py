r"""
Points on projective varieties

Scheme morphism for points on projective varieties



AUTHORS:

- David Kohel, William Stein

- William Stein (2006-02-11): fixed bug where P(0,0,0) was allowed as
  a projective point.

- Volker Braun (2011-08-08): Renamed classes, more documentation, misc
  cleanups.

- Ben Hutz (June 2012) added support for projective ring;
  (March 2013) iteration functionality and new directory structure
  for affine/projective, height functionality
"""

# Historical note: in trac #11599, V.B. renamed
# * _point_morphism_class -> _morphism
# * _homset_class -> _point_homset

#*****************************************************************************
#       Copyright (C) 2011 Volker Braun <vbraun.name@gmail.com>
#       Copyright (C) 2006 David Kohel <kohel@maths.usyd.edu.au>
#       Copyright (C) 2006 William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.categories.number_fields import NumberFields
_NumberFields = NumberFields()
from sage.rings.infinity       import infinity
from sage.rings.arith          import gcd, lcm, is_prime, binomial
from sage.rings.integer_ring   import ZZ
from sage.rings.fraction_field import FractionField
from sage.rings.morphism       import RingHomomorphism_im_gens
from sage.rings.number_field.order import is_NumberFieldOrder
from sage.rings.number_field.number_field_ideal import NumberFieldFractionalIdeal
from sage.rings.padics.all     import Qp
from sage.rings.quotient_ring  import QuotientRing_generic
from sage.rings.rational_field import QQ
from sage.rings.real_double    import RDF
from sage.rings.real_mpfr      import RealField, RR, is_RealField

from copy                      import copy
from sage.schemes.generic.morphism import (SchemeMorphism,
                                           is_SchemeMorphism,
                                           SchemeMorphism_point)
from sage.structure.element    import AdditiveGroupElement
from sage.structure.sequence   import Sequence



#*******************************************************************
# Projective varieties
#*******************************************************************
class SchemeMorphism_point_projective_ring(SchemeMorphism_point):
    """
    A rational point of projective space over a ring.

    INPUT:

    -  ``X`` -- a homset of a subscheme of an ambient projective space over a field `K`

    - ``v`` -- a list or tuple of coordinates in `K`

    - ``check`` -- boolean (optional, default:``True``). Whether to check the input for consistency.

    EXAMPLES::

        sage: P = ProjectiveSpace(2, ZZ)
        sage: P(2,3,4)
        (2 : 3 : 4)

    """

    def __init__(self, X, v, check=True):
        """
        The Python constructor.

        EXAMPLES::

            sage: P = ProjectiveSpace(2, QQ)
            sage: P(2, 3/5, 4)
            (1/2 : 3/20 : 1)

        ::

            sage: P = ProjectiveSpace(1, ZZ)
            sage: P([0, 1])
            (0 : 1)

        ::

            sage: P = ProjectiveSpace(1, ZZ)
            sage: P([0, 0, 1])
            Traceback (most recent call last):
            ...
            TypeError: v (=[0, 0, 1]) must have 2 components

        ::

            sage: P = ProjectiveSpace(3, QQ)
            sage: P(0,0,0,0)
            Traceback (most recent call last):
            ...
            ValueError: [0, 0, 0, 0] does not define a valid point since all entries are 0

        ::

        It is possible to avoid the possibly time consuming checks, but be careful!!

            sage: P = ProjectiveSpace(3, QQ)
            sage: P.point([0,0,0,0],check=False)
            (0 : 0 : 0 : 0)

        ::

            sage: P.<x, y, z> = ProjectiveSpace(2, ZZ)
            sage: X=P.subscheme([x^2-y*z])
            sage: X([2,2,2])
            (2 : 2 : 2)
        """
        SchemeMorphism.__init__(self, X)
        if check:
            from sage.schemes.elliptic_curves.ell_point import EllipticCurvePoint_field
            d = X.codomain().ambient_space().ngens()
            if is_SchemeMorphism(v) or isinstance(v, EllipticCurvePoint_field):
                v = list(v)
            elif v is infinity:
                v = [0] * (d)
                v[1] = 1
            if not isinstance(v,(list,tuple)):
                raise TypeError("Argument v (= %s) must be a scheme point, list, or tuple."%str(v))
            if len(v) != d and len(v) != d-1:
                raise TypeError("v (=%s) must have %s components"%(v, d))

            R = X.value_ring()
            v = Sequence(v, R)
            if len(v) == d-1:     # very common special case
                v.append(1)

            n = len(v)
            all_zero = True
            for i in range(n):
                last = n-1-i
                if v[last]:
                    all_zero = False
                    break
            if all_zero:
                raise ValueError("%s does not define a valid point since all entries are 0"%repr(v))

            X.extended_codomain()._check_satisfies_equations(v)

            if isinstance(X.codomain().base_ring(), QuotientRing_generic):
                lift_coords = [P.lift() for P in v]
            else:
                lift_coords = v
            v = Sequence(lift_coords)

        self._coords = v

    def __eq__(self,right):
        """
        Tests the proejctive equality of two points.

        INPUT:

        - ``right`` - a point on projective space

        OUTPUT:

        - Boolean - True if ``self`` and ``right`` define the same point. False otherwise.

        Examples::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([1,2])
            sage: Q=PS([2,4])
            sage: P==Q
            True

        ::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([1,2])
            sage: Q=PS([1,0])
            sage: P==Q
            False

        ::

            sage: PS=ProjectiveSpace(Zp(5),1,'x')
            sage: P=PS([0,1])
            sage: P==0
            True

        ::

            sage: R.<t>=PolynomialRing(QQ)
            sage: PS=ProjectiveSpace(R,1,'x')
            sage: P=PS([t,1+t^2])
            sage: Q=PS([t^2, t+t^3])
            sage: P==Q
            True

        ::

            sage: PS=ProjectiveSpace(ZZ,2,'x')
            sage: P=PS([0,1,2])
            sage: P==0
            False

        ::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([2,1])
            sage: PS2=ProjectiveSpace(Zp(7),1,'x')
            sage: Q=PS2([2,1])
            sage: P==Q
            False

        ::

            sage: PS=ProjectiveSpace(ZZ.quo(6),2,'x')
            sage: P=PS([2,4,1])
            sage: Q=PS([0,1,3])
            sage: P==Q
            False

        ::

            sage: R.<z>=PolynomialRing(QQ)
            sage: K.<t>=NumberField(z^2+5)
            sage: OK=K.ring_of_integers()
            sage: t=OK.gen(1)
            sage: PS.<x,y>=ProjectiveSpace(OK,1)
            sage: P=PS(2,1+t)
            sage: Q=PS(1-t,3)
            sage: P==Q
            True

        """
        if not isinstance(right, SchemeMorphism_point):
            try:
                right = self.codomain()(right)
            except TypeError:
                return False
        if self.codomain()!=right.codomain():
            return False
        n=len(self._coords)
        for i in range(0,n):
            for j in range(i+1,n):
                if self._coords[i]*right._coords[j] != self._coords[j]*right._coords[i]:
                    return False
        return True

    def __ne__(self,right):
        """
        Tests the proejctive equality of two points.

        INPUT:

        - ``right`` - a point on projective space

        OUTPUT:

        - Boolean - True if ``self`` and ``right`` define different points. False otherwise.

        Examples::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([1,2])
            sage: Q=PS([2,4])
            sage: P!=Q
            False

        ::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([1,2])
            sage: Q=PS([1,0])
            sage: P!=Q
            True

        ::

            sage: PS=ProjectiveSpace(Zp(5),1,'x')
            sage: P=PS([0,1])
            sage: P!=0
            False

        ::

            sage: R.<t>=PolynomialRing(QQ)
            sage: PS=ProjectiveSpace(R,1,'x')
            sage: P=PS([t,1+t^2])
            sage: Q=PS([t^2, t+t^3])
            sage: P!=Q
            False

        ::

            sage: PS=ProjectiveSpace(ZZ,2,'x')
            sage: P=PS([0,1,2])
            sage: P!=0
            True

        ::

            sage: PS=ProjectiveSpace(ZZ,1,'x')
            sage: P=PS([2,1])
            sage: PS2=ProjectiveSpace(Zp(7),1,'x')
            sage: Q=PS2([2,1])
            sage: P!=Q
            True

        ::

            sage: PS=ProjectiveSpace(ZZ.quo(6),2,'x')
            sage: P=PS([2,4,1])
            sage: Q=PS([0,1,3])
            sage: P!=Q
            True
        """
        if not isinstance(right, SchemeMorphism_point):
            try:
                right = self.codomain()(right)
            except TypeError:
                return True
        if self.codomain()!=right.codomain():
            return True
        n=len(self._coords)
        for i in range(0,n):
            for j in range(i+1,n):
                if self._coords[i]*right._coords[j] != self._coords[j]*right._coords[i]:
                    return True
        return False

    def scale_by(self,t):
        """
        Scale the coordinates of the point ``self`` by `t`. A ``TypeError`` occurs if
        the point is not in the base_ring of the codomain after scaling.

        INPUT:

        - ``t`` -- a ring element

        OUTPUT:

        - None.

        EXAMPLES::

            sage: R.<t>=PolynomialRing(QQ)
            sage: P=ProjectiveSpace(R,2,'x')
            sage: p=P([3/5*t^3,6*t, t])
            sage: p.scale_by(1/t); p
            (3/5*t^2 : 6 : 1)

        ::

            sage: R.<t>=PolynomialRing(QQ)
            sage: S=R.quo(R.ideal(t^3))
            sage: P.<x,y,z>=ProjectiveSpace(S,2)
            sage: Q=P(t,1,1)
            sage: Q.scale_by(t);Q
            (tbar^2 : tbar : tbar)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: Q=P(2,2,2)
            sage: Q.scale_by(1/2);Q
            (1 : 1 : 1)
        """
        if t==0:  #what if R(t) == 0 ?
            raise ValueError("Cannot scale by 0")
        R=self.codomain().base_ring()
        if isinstance(R, QuotientRing_generic):
            phi=R._internal_coerce_map_from(self.codomain().ambient_space().base_ring())
            for i in range(self.codomain().ambient_space().dimension_relative()+1):
                self._coords[i]=phi(self._coords[i]*t).lift()
        else:
            for i in range(self.codomain().ambient_space().dimension_relative()+1):
                self._coords[i]=R(self._coords[i]*t)

    def normalize_coordinates(self):
        """
        Removes the gcd from the coordinates of ``self`` (including `-1`).

        .. WARNING:: The gcd will depend on the base ring.

        OUTPUT:

        - None.

        EXAMPLES::

            sage: P = ProjectiveSpace(ZZ,2,'x')
            sage: p = P([-5,-15,-20])
            sage: p.normalize_coordinates(); p
            (1 : 3 : 4)

        ::

            sage: P = ProjectiveSpace(Zp(7),2,'x')
            sage: p = P([-5,-15,-2])
            sage: p.normalize_coordinates(); p
            (5 + O(7^20) : 1 + 2*7 + O(7^20) : 2 + O(7^20))

        ::

            sage: R.<t> = PolynomialRing(QQ)
            sage: P = ProjectiveSpace(R,2,'x')
            sage: p = P([3/5*t^3,6*t, t])
            sage: p.normalize_coordinates(); p
            (3/5*t^2 : 6 : 1)

        ::

            sage: P.<x,y> = ProjectiveSpace(Zmod(20),1)
            sage: Q = P(4,8)
            sage: Q.normalize_coordinates()
            sage: Q
            (1 : 2)

        ::

            sage: R.<t> = PolynomialRing(QQ,1)
            sage: S = R.quotient_ring(R.ideal(t^3))
            sage: P.<x,y> = ProjectiveSpace(S,1)
            sage: Q = P(t,t^2)
            sage: Q.normalize_coordinates()
            sage: Q
            (1 : t)

        Since the base ring is a polynomial ring over a field, only the
        gcd `c` is removed. ::

            sage: R.<c> = PolynomialRing(QQ)
            sage: P = ProjectiveSpace(R,1)
            sage: Q = P(2*c,4*c)
            sage: Q.normalize_coordinates();Q
            (2 : 4)

        A polynomial ring over a ring gives the more intuitive result. ::

            sage: R.<c> = PolynomialRing(ZZ)
            sage: P = ProjectiveSpace(R,1)
            sage: Q = P(2*c,4*c)
            sage: Q.normalize_coordinates();Q
            (1 : 2)
        """
        R=self.codomain().base_ring()
        GCD = R(gcd(self[0],self[1]))
        index=2
        if self[0]>0 or self[1] >0:
            neg=0
        else:
            neg=1
        while GCD!=1 and index < len(self._coords):
            if self[index]>0:
                neg=0
            GCD=R(gcd(GCD,self[index]))
            index+=1
        if isinstance(R,(QuotientRing_generic)):
            R=R.cover_ring()
            GCD=GCD.lift()
        if GCD != 1:
            if neg==1:
                self.scale_by(R(-1)/GCD)
            else:
                self.scale_by(R(1)/GCD)
        else:
            if neg==1:
                self.scale_by(R(-1))

    def dehomogenize(self,n):
        r"""
        Dehomogenizes at the nth coordinate

        INPUT:

        - ``n`` -- non-negative integer

        OUTPUT:

        - :class:`SchemeMorphism_point_affine`

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: X=P.subscheme(x^2-y^2);
            sage: Q=X(23,23,46)
            sage: Q.dehomogenize(2)
            (1/2, 1/2)

        ::

            sage: R.<t>=PolynomialRing(QQ)
            sage: S=R.quo(R.ideal(t^3))
            sage: P.<x,y,z>=ProjectiveSpace(S,2)
            sage: Q=P(t,1,1)
            sage: Q.dehomogenize(1)
            (tbar, 1)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(GF(5),2)
            sage: Q=P(1,3,1)
            sage: Q.dehomogenize(0)
            (3, 1)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(GF(5),2)
            sage: Q=P(1,3,0)
            sage: Q.dehomogenize(2)
            Traceback (most recent call last):
            ...
            ValueError: Can't dehomogenize at 0 coordinate.
        """
        if self[n]==0:
            raise ValueError("Can't dehomogenize at 0 coordinate.")
        PS=self.codomain()
        A=PS.affine_patch(n)
        Q=[]
        for i in range(0,PS.ambient_space().dimension_relative()+1):
            if i !=n:
                Q.append(self[i]/self[n])
        return(A.point(Q))

    def nth_iterate(self,f,n,normalize=False):
        r"""
        For a map ``self`` and a point `P` in ``self.domain()``
        this function returns the nth iterate of `P` by ``self``. If ``normalize==True``,
        then the coordinates are automatically normalized.

        INPUT:

        - ``f`` -- a SchmemMorphism_polynomial with ``self`` in ``f.domain()``

        - ``n`` -- a positive integer.

        - ``normalize`` -- Boolean (optional Default: ``False``)

        OUTPUT:

        - A point in ``self.codomain()``

        EXAMPLES::

            sage: P.<x,y>=ProjectiveSpace(ZZ,1)
            sage: H=Hom(P,P)
            sage: f=H([x^2+y^2,2*y^2])
            sage: P(1,1).nth_iterate(f,4)
            (32768 : 32768)

        ::

            sage: P.<x,y>=ProjectiveSpace(ZZ,1)
            sage: H=Hom(P,P)
            sage: f=H([x^2+y^2,2*y^2])
            sage: P(1,1).nth_iterate(f,4,1)
            (1 : 1)

        ::

            sage: R.<t>=PolynomialRing(QQ)
            sage: P.<x,y,z>=ProjectiveSpace(R,2)
            sage: H=Hom(P,P)
            sage: f=H([x^2+t*y^2,(2-t)*y^2,z^2])
            sage: P(2+t,7,t).nth_iterate(f,2)
            (t^4 + 2507*t^3 - 6787*t^2 + 10028*t + 16 : -2401*t^3 + 14406*t^2 -
            28812*t + 19208 : t^4)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: X=P.subscheme(x^2-y^2)
            sage: H=Hom(X,X)
            sage: f=H([x^2,y^2,z^2])
            sage: X(2,2,3).nth_iterate(f,3)
            (256 : 256 : 6561)

        .. TODO:: Is there a more efficient way to do this?
        """
        if self.codomain()!=f.domain():
            raise TypeError("Point is not defined over domain of function")
        if f.domain() != f.codomain():
            raise TypeError("Domain and Codomain of function not equal")
        try:
            n=ZZ(n)
        except TypeError:
            raise TypeError("Iterate number must be an integer")
        if n <0:
            raise TypeError("Must be a forward orbit")
        if n==0:
            return(self)
        else:
            Q=f(self)
            if normalize==True:
                Q.normalize_coordinates()
            for i in range(2,n+1):
                Q=f(Q)
                if normalize==True:
                    Q.normalize_coordinates()
            return(Q)

    def orbit(self,f,N,**kwds):
        r"""
        Returns the orbit of `P` by ``self``. If `n` is an integer it returns `[P,self(P),\ldots,self^n(P)]`.
        If `n` is a list or tuple `n=[m,k]` it returns `[self^m(P),\ldots,self^k(P)`].
        Automatically normalize the points if ``normalize=True``. Perform the checks on point initialization if
        ``check=True``

        INPUT:

        - ``f`` -- a :class:`SchemeMorphism_polynomial` with ``self`` in ``f.domain()``

        - ``N`` -- a non-negative integer or list or tuple of two non-negative integers

        kwds:

        - ``check`` -- boolean (optional - default: ``True``)

        - ``normalize`` -- boolean (optional - default: ``False``)


        OUTPUT:

        - a list of points in ``self.codomain()``

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: H=Hom(P,P)
            sage: f=H([x^2+y^2,y^2-z^2,2*z^2])
            sage: P(1,2,1).orbit(f,3)
            [(1 : 2 : 1), (5 : 3 : 2), (34 : 5 : 8), (1181 : -39 : 128)]

        ::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: H=Hom(P,P)
            sage: f=H([x^2+y^2,y^2-z^2,2*z^2])
            sage: P(1,2,1).orbit(f,[2,4])
            [(34 : 5 : 8), (1181 : -39 : 128), (1396282 : -14863 : 32768)]

        ::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: X=P.subscheme(x^2-y^2)
            sage: H=Hom(X,X)
            sage: f=H([x^2,y^2,x*z])
            sage: X(2,2,3).orbit(f,3,normalize=True)
            [(2 : 2 : 3), (2 : 2 : 3), (2 : 2 : 3), (2 : 2 : 3)]

        ::

            sage: P.<x,y>=ProjectiveSpace(QQ,1)
            sage: H=Hom(P,P)
            sage: f=H([x^2+y^2,y^2])
            sage: P.point([1,2],False).orbit(f,4,check=False)
            [(1 : 2), (5 : 4), (41 : 16), (1937 : 256), (3817505 : 65536)]
        """
        if (isinstance(N,(list,tuple))==False):
            N=[0,N]
        try:
            N[0]=ZZ(N[0])
            N[1]=ZZ(N[1])
        except TypeError:
            raise TypeError("Orbit bounds must be integers")
        if N[0]<0 or N[1] <0:
            raise TypeError("Orbit bounds must be non-negative")
        if N[0] > N[1]:
            return([])

        Q=copy(self)
        check = kwds.pop("check",True)
        normalize = kwds.pop("normalize",False)

        if normalize==True:
            Q.normalize_coordinates()
        for i in range(1,N[0]+1):
            Q=f(Q,check)
            if normalize==True:
                Q.normalize_coordinates()
        Orb=[Q]
        for i in range(N[0]+1,N[1]+1):
            Q=f(Q,check)
            if normalize==True:
                Q.normalize_coordinates()
            Orb.append(Q)
        return(Orb)

    def green_function(self, G, v, **kwds):
        r"""
        Evaluates the local Green's function at the place ``v`` for ``P`` with ``N`` terms of the
        series or to within a given error bound.  Must be over a number field
        or order of a number field. Note that this is absolute local greens function
        so is scaled by the degree of the base field.

        Use ``v=0`` for the archimedean place over `\QQ` or field embedding. Non-archimedean
        places are prime ideals for number fields or primes over `\QQ`.

        ALGORITHM:

        See Exercise 5.29 and Figure 5.6 of ``The Arithmetic of Dynamics Systems``, Joseph H. Silverman, Springer, GTM 241, 2007.

        INPUT:

        - ``P`` - a projective point

        - ``v`` - non-negative integer. a place, use v=0 for the archimedean place

        kwds:

        - ``N`` - positive integer. number of terms of the series to use, default: 10

        - ``prec`` - positive integer, float point or p-adic precision, default: 100

        - ``error_bound`` - a positive real number

        OUTPUT:

        - a real number

        EXAMPLES::

            sage: K.<w> = QuadraticField(3)
            sage: P.<x,y> = ProjectiveSpace(K,1)
            sage: H = Hom(P,P)
            sage: f = H([17*x^2+1/7*y^2,17*w*x*y])
            sage: f.green_function(P.point([w,2],False), K.places()[1])
            1.7236334013785676107373093775
            sage: print f.green_function(P([2,1]), K.ideal(7), N=7)
            0.48647753726382832627633818586
            sage: print f.green_function(P([w,1]), K.ideal(17), error_bound=0.001)
            -0.70761163353747779889947530309

        .. TODO:: Implement general p-adic extensions so that the flip trick can be used
             for number fields.
        """
        N = kwds.get('N', 10)                     #Get number of iterates (if entered)
        err = kwds.get('error_bound', None)         #Get error bound (if entered)
        prec = kwds.get('prec', 100)                #Get precision (if entered)
        R = RealField(prec)
        localht = R(0)
        BR = FractionField(self.codomain().base_ring())
        GBR = G.change_ring(BR) #so the heights work

        if not BR in NumberFields():
            raise NotImplementedError("Must be over a NumberField or a NumberField Order")

        #For QQ the 'flip-trick' works better over RR or Qp
        if isinstance(v, (NumberFieldFractionalIdeal, RingHomomorphism_im_gens)):
            K = BR
        elif is_prime(v):
            K = Qp(v, prec)
        elif v == 0:
            K = R
            v = BR.places(prec=prec)[0]
        else:
            raise ValueError("Invalid valuation (=%s) entered."%v)

        #Coerce all polynomials in F into polynomials with coefficients in K
        F = G.change_ring(K, False)
        d = F.degree()
        dim = F.codomain().ambient_space().dimension_relative()
        P = self.change_ring(K, False)

        if err is not None:
            err = R(err)
            if not err>0:
                raise ValueError("Error bound (=%s) must be positive."%err)
            if G.is_endomorphism() == False:
                raise NotImplementedError("Error bounds only for endomorphisms")

            #if doing error estimates, compute needed number of iterates
            D = (dim + 1) * (d - 1) + 1
            #compute upper bound
            if isinstance(v, RingHomomorphism_im_gens): #archimedean
                vindex = BR.places(prec=prec).index(v)
                U = GBR.local_height_arch(vindex, prec=prec) + R(binomial(dim + d, d)).log()
            else: #non-archimedean
                U = GBR.local_height(v, prec=prec)

            #compute lower bound - from explicit polynomials of Nullstellensatz
            CR = GBR.codomain().ambient_space().coordinate_ring() #.lift() only works over fields
            I = CR.ideal(GBR.defining_polynomials())
            maxh = 0
            for k in range(dim + 1):
                CoeffPolys = (CR.gen(k) ** D).lift(I)
                Res = 1
                h = 1
                for poly in CoeffPolys:
                    if poly != 0:
                        for c in poly.coefficients():
                            Res = lcm(Res, c.denominator())
                for poly in CoeffPolys:
                    if poly != 0:
                        if isinstance(v, RingHomomorphism_im_gens): #archimedean
                            if BR == QQ:
                                h = max([(Res*c).local_height_arch(prec=prec) for c in poly.coefficients()])
                            else:
                                h = max([(Res*c).local_height_arch(vindex, prec=prec) for c in poly.coefficients()])
                        else: #non-archimedean
                            h = max([c.local_height(v, prec=prec) for c in poly.coefficients()])
                        if h > maxh:
                            maxh=h
            if isinstance(v, RingHomomorphism_im_gens): #archimedean
                L = R(Res / ((dim + 1) * binomial(dim + D - d, D - d) * maxh)).log().abs()
            else: #non-archimedean
                L = R(1 / maxh).log().abs()
            C = max([U, L])
            if C != 0:
                N = R(C/(err)).log(d).abs().ceil()
            else: #we just need log||P||_v
                N=1

        #START GREEN FUNCTION CALCULATION
        if isinstance(v, RingHomomorphism_im_gens):  #embedding for archimedean local height
            for i in range(N+1):
                Pv = [ (v(t).abs()) for t in P ]
                m = -1
                #compute the maximum absolute value of entries of a, and where it occurs
                for n in range(dim + 1):
                    if Pv[n] > m:
                        j = n
                        m = Pv[n]
                # add to sum for the Green's function
                localht += ((1/R(d))**R(i)) * (R(m).log())
                #get the next iterate
                if i < N:
                    P.scale_by(1/P[j])
                    P = F(P, False)
            return (1/BR.absolute_degree()) * localht

        #else - prime or prime ideal for non-archimedean
        for i in range(N + 1):
            if BR == QQ:
                Pv = [ R(K(t).abs()) for t in P ]
            else:
                Pv = [ R(t.abs_non_arch(v)) for t in P ]
            m = -1
            #compute the maximum absolute value of entries of a, and where it occurs
            for n in range(dim + 1):
                if Pv[n] > m:
                    j = n
                    m = Pv[n]
            # add to sum for the Green's function
            localht += ((1/R(d))**R(i)) * (R(m).log())
            #get the next iterate
            if i < N:
                P.scale_by(1/P[j])
                P = F(P, False)
        return (1/BR.absolute_degree()) * localht

    def canonical_height(self, F, **kwds):
        r"""
        Evaluates the (absolute) canonical height of ``self`` with respect to ``F``. Must be over number field
        or order of a number field. Specify either the number of terms of the series to evaluate or
        the error bound required.

        ALGORITHM:

            The sum of the Green's function at the archimedean places and the places of bad reduction.

        INPUT:

        - ``P`` - a projective point

        kwds:

        - ``badprimes`` - a list of primes of bad reduction

        - ``N`` - positive integer. number of terms of the series to use in the local green functions

        - ``prec`` - positive integer, float point or p-adic precision

        - ``error_bound`` - a positive real number

        OUTPUT:

        - a real number

        EXAMPLES::

            sage: P.<x,y> = ProjectiveSpace(ZZ,1)
            sage: H = Hom(P,P)
            sage: f = H([x^2+y^2,2*x*y]);
            sage: Q = P(2,1)
            sage: f.canonical_height(f(Q))
            2.1965476757927038111992627081
            sage: f.canonical_height(Q)
            1.0979353871245941198040174712

        Notice that preperiodic points may not be exactly 0. ::

            sage: P.<x,y> = ProjectiveSpace(QQ,1)
            sage: H = Hom(P,P)
            sage: f = H([x^2-29/16*y^2,y^2]);
            sage: Q = P(5,4)
            sage: f.canonical_height(Q, N=30)
            1.4989058602918874235833076226e-9

        ::

            sage: P.<x,y,z> = ProjectiveSpace(QQ,2)
            sage: X = P.subscheme(x^2-y^2);
            sage: H = Hom(X,X)
            sage: f = H([x^2,y^2,30*z^2]);
            sage: Q = X([4,4,1])
            sage: f.canonical_height(Q, badprimes=[2,3,5], prec=200)
            2.7054056208276961889784303469356774912979228770208655455481
        """
        bad_primes = kwds.pop("badprimes", None)
        prec = kwds.get("prec", 100)
        error_bound = kwds.get("error_bound", None)
        K = FractionField(self.codomain().base_ring())

        if not K in _NumberFields:
            raise NotImplementedError("Must be over a NumberField or a NumberField Order")

        if bad_primes is None:
            bad_primes = []
            for b in self:
                if K == QQ:
                    bad_primes += b.denominator().prime_factors()
                else:
                    bad_primes += b.denominator_ideal().prime_factors()
            bad_primes += K(F.resultant()).support()
            bad_primes = list(set(bad_primes))

        emb = K.places(prec=prec)
        num_places = len(emb) + len(bad_primes)
        if not error_bound is None:
            error_bound /= num_places
        R = RealField(prec)
        h = R(0)

        # Archimedean local heights
        # :: WARNING: If places is fed the default Sage precision of 53 bits,
        # it uses Real or Complex Double Field in place of RealField(prec) or ComplexField(prec)
        # the function is_RealField does not identify RDF as real, so we test for that ourselves.
        for v in emb:
            if is_RealField(v.codomain()) or v.codomain() is RDF:
                dv = R(1)
            else:
                dv = R(2)
            h += dv*self.green_function(F, v, **kwds)       #arch Green function

        # Non-Archimedean local heights
        for v in bad_primes:
            if K == QQ:
                dv = R(1)
            else:
                dv = R(v.residue_class_degree() * v.absolute_ramification_index())
            h += dv * self.green_function(F, v, **kwds)  #non-arch Green functions
        return h

    def global_height(self, prec=None):
        r"""
        Returns the logarithmic height of the points.

        INPUT:

        - ``prec`` -- desired floating point precision (default:
          default RealField precision).

        OUTPUT:

        - a real number

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: Q=P.point([4,4,1/30])
            sage: Q.global_height()
            4.78749174278205

        ::

            sage: P.<x,y,z>=ProjectiveSpace(ZZ,2)
            sage: Q=P([4,1,30])
            sage: Q.global_height()
            3.40119738166216

        ::

            sage: R.<x>=PolynomialRing(QQ)
            sage: k.<w>=NumberField(x^2+5)
            sage: A=ProjectiveSpace(k,2,'z')
            sage: A([3,5*w+1,1]).global_height(prec=100)
            2.4181409534757389986565376694

        """
        if self.domain().base_ring() in _NumberFields or is_NumberFieldOrder(self.domain().base_ring()):
            return(max([self[i].global_height(prec=prec) for i in range(self.codomain().ambient_space().dimension_relative()+1)]))
        else:
            raise TypeError("Must be over a Numberfield or a Numberfield Order")

    def local_height(self, v, prec=None):
        r"""
        Returns the maximum of the local height of the coordinates of ``self``.

        INPUT:

        - ``v`` -- a prime or prime ideal of the base ring

        - ``prec`` -- desired floating point precision (default:
          default RealField precision).

        OUTPUT:

        - a real number

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: Q=P.point([4,4,1/150],False)
            sage: Q.local_height(5)
            3.21887582486820

        ::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: Q=P([4,1,30])
            sage: Q.local_height(2)
            0.693147180559945
        """
        K = FractionField(self.domain().base_ring())
        if K not in _NumberFields:
            raise("Must be over a Numberfield or a Numberfield Order")
        return max([K(c).local_height(v, prec=prec) for c in self])

    def local_height_arch(self, i, prec=None):
        r"""
        Returns the maximum of the local heights at the ``i``-th infinite place of ``self``.

        INPUT:

        - ``i`` -- an integer

        - ``prec`` -- desired floating point precision (default:
          default RealField precision).

        OUTPUT:

        - a real number

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: Q = P.point([4,4,1/150], False)
            sage: Q.local_height_arch(0)
            1.38629436111989

        ::

            sage: P.<x,y,z>=ProjectiveSpace(QuadraticField(5, 'w'),2)
            sage: Q = P.point([4,1,30], False)
            sage: Q.local_height_arch(1)
            3.401197381662155375413236691607
        """
        K = FractionField(self.domain().base_ring())
        if K not in _NumberFields:
            raise("Must be over a Numberfield or a Numberfield Order")
        if K == QQ:
            return max([K(c).local_height_arch(prec=prec) for c in self])
        else:
            return max([K(c).local_height_arch(i, prec=prec) for c in self])

    def multiplier(self,f,n,check=True):
        r"""
        Returns the multiplier of the projective point ``self`` of period `n` by the function `f`.
        `f` must be an endomorphism of projective space

        INPUT:

        - ``f`` - a endomorphism of ``self.codomain()``

        - ``n`` - a positive integer, the period of ``self``

        - ``check`` -- check if ``P`` is periodic of period ``n``, Default:True

        OUTPUT:

        - a square matrix of size ``self.codomain().dimension_relative()`` in the ``base_ring`` of ``self``

        EXAMPLES::

            sage: P.<x,y,z,w>=ProjectiveSpace(QQ,3)
            sage: H=Hom(P,P)
            sage: f=H([x^2,y^2,4*w^2,4*z^2]);
            sage: Q=P.point([4,4,1,1],False);
            sage: Q.multiplier(f,1)
            [ 2  0 -8]
            [ 0  2 -8]
            [ 0  0 -2]
        """
        return(f.multiplier(self,n,check))

class SchemeMorphism_point_projective_field(SchemeMorphism_point_projective_ring):
    """
    A rational point of projective space over a field.

    INPUT:

    -  ``X`` -- a homset of a subscheme of an ambient projective space
       over a field `K`

    - ``v`` -- a list or tuple of coordinates in `K`

    - ``check`` -- boolean (optional, default:``True``). Whether to
      check the input for consistency.

    EXAMPLES::

        sage: P = ProjectiveSpace(3, RR)
        sage: P(2,3,4,5)
        (0.400000000000000 : 0.600000000000000 : 0.800000000000000 : 1.00000000000000)
    """

    def __init__(self, X, v, check=True):
        """
        The Python constructor.

        See :class:`SchemeMorphism_point_projective_ring` for details.

        This function still normalized points so that the rightmost non-zero coordinate is 1. The is to maintain current functionality with current
        implementations of curves in projectives space (plane, connic, elliptic, etc). The class:`SchemeMorphism_point_projective_ring` is for general use.

        EXAMPLES::

            sage: P = ProjectiveSpace(2, QQ)
            sage: P(2, 3/5, 4)
            (1/2 : 3/20 : 1)

        ::

            sage: P = ProjectiveSpace(3, QQ)
            sage: P(0,0,0,0)
            Traceback (most recent call last):
            ...
            ValueError: [0, 0, 0, 0] does not define a valid point since all entries are 0

        ::

            sage: P.<x, y, z> = ProjectiveSpace(2, QQ)
            sage: X=P.subscheme([x^2-y*z])
            sage: X([2,2,2])
            (1 : 1 : 1)
        """
        SchemeMorphism.__init__(self, X)
        if check:
            from sage.schemes.elliptic_curves.ell_point import EllipticCurvePoint_field
            d = X.codomain().ambient_space().ngens()
            if is_SchemeMorphism(v) or isinstance(v, EllipticCurvePoint_field):
                v = list(v)
            elif v is infinity:
                v = [0] * (d)
                v[1] = 1
            if not isinstance(v,(list,tuple)):
                raise TypeError("Argument v (= %s) must be a scheme point, list, or tuple."%str(v))
            if len(v) != d and len(v) != d-1:
                raise TypeError("v (=%s) must have %s components"%(v, d))

            R = X.value_ring()
            v = Sequence(v, R)
            if len(v) == d-1:     # very common special case
                v.append(1)

            n = len(v)
            all_zero = True
            for i in range(n):
                last = n-1-i
                if v[last]:
                    all_zero = False
                    c = v[last]
                    if c == R.one():
                        break
                    for j in range(last):
                        v[j] /= c
                    v[last] = R.one()
                    break
            if all_zero:
                raise ValueError("%s does not define a valid point since all entries are 0"%repr(v))

            X.extended_codomain()._check_satisfies_equations(v)

        self._coords = v

    def normalize_coordinates(self):
        r"""
        Normalizes ``self`` so that the last non-zero coordinate is `1`.

        OUTPUT: None.

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(GF(5),2)
            sage: Q=P.point([1,3,0],false);Q
            (1 : 3 : 0)
            sage: Q.normalize_coordinates();Q
            (2 : 1 : 0)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: X=P.subscheme(x^2-y^2);
            sage: Q=X.point([23,23,46], false);Q
            (23 : 23 : 46)
            sage: Q.normalize_coordinates();Q
            (1/2 : 1/2 : 1)
        """
        index=self.codomain().ambient_space().dimension_relative()
        while self[index]==0:
            index-=1
        self.scale_by(1/self[index])


    def clear_denominators(self):
        r"""
        scales by the least common multiple of the denominators.

        OUTPUT: None.

        EXAMPLES::

            sage: R.<t>=PolynomialRing(QQ)
            sage: P.<x,y,z>=ProjectiveSpace(FractionField(R),2)
            sage: Q=P([t,3/t^2,1])
            sage: Q.clear_denominators(); Q
            (t^3 : 3 : t^2)

        ::

            sage: R.<x>=PolynomialRing(QQ)
            sage: K.<w>=NumberField(x^2-3)
            sage: P.<x,y,z>=ProjectiveSpace(K,2)
            sage: Q=P([1/w,3,0])
            sage: Q.clear_denominators(); Q
            (w : 9 : 0)

        ::

            sage: P.<x,y,z>=ProjectiveSpace(QQ,2)
            sage: X=P.subscheme(x^2-y^2);
            sage: Q=X([1/2,1/2,1]);
            sage: Q.clear_denominators(); Q
            (1 : 1 : 2)
        """
        self.scale_by(lcm([self[i].denominator() for i in range(self.codomain().ambient_space().dimension_relative())]))

class SchemeMorphism_point_projective_finite_field(SchemeMorphism_point_projective_field):

    def __hash__(self):
        r"""
        Returns the integer hash of ``self``


        OUTPUT:

        - integer

        EXAMPLES::

            sage: P.<x,y,z>=ProjectiveSpace(GF(5),2)
            sage: hash(P(2,1,2))
            41

        ::

            sage: P.<x,y,z>=ProjectiveSpace(GF(7),2)
            sage: X=P.subscheme(x^2-y^2)
            sage: hash(X(1,1,2))
            81

        ::

            sage: P.<x,y>=ProjectiveSpace(GF(13),1)
            sage: hash(P(3,4))
            17

        ::

            sage: P.<x,y>=ProjectiveSpace(GF(13^3,'t'),1)
            sage: hash(P(3,4))
            2201
        """
        p=self.codomain().base_ring().order()
        N=self.codomain().ambient_space().dimension_relative()
        return sum(hash(self[i])*p**i for i in range(N+1))

    def orbit_structure(self,f):
        r"""
        Every point is preperiodic over a finite field. This function returns the pair `[m,n]` where `m` is the
        preperiod and `n` is the period of the point ``self`` by ``f``.

        INPUT:

        - ``f`` -- a :class:`ScemeMorphism_polynomial` with ``self`` in ``f.domain()``

        OUTPUT:

        - a list `[m,n]` of integers

        EXAMPLES::

            sage: P.<x,y,z> = ProjectiveSpace(GF(5),2)
            sage: H = Hom(P,P)
            sage: f = H([x^2 + y^2,y^2,z^2 + y*z])
            sage: P(1,0,1).orbit_structure(f)
            [0, 1]

        ::

            sage: P.<x,y,z> = ProjectiveSpace(GF(17),2)
            sage: X = P.subscheme(x^2-y^2)
            sage: H = Hom(X,X)
            sage: f = H([x^2,y^2,z^2])
            sage: X(1,1,2).orbit_structure(f)
            [3, 1]

        ::

            sage: R.<t> = GF(13^3)
            sage: P.<x,y> = ProjectiveSpace(R,1)
            sage: H = Hom(P,P)
            sage: f = H([x^2 - y^2,y^2])
            sage: P(t,4).orbit_structure(f)
            [11, 6]
        """
        Orbit=[]
        index=1
        P=copy(self)
        P.normalize_coordinates()
        F=copy(f)
        F.normalize_coordinates()
        while not P in Orbit:
            Orbit.append(P)
            P=F(P)
            P.normalize_coordinates()
            index+=1
        I=Orbit.index(P)
        return([I,index-I-1])

#*******************************************************************
# Abelian varieties
#*******************************************************************
class SchemeMorphism_point_abelian_variety_field(AdditiveGroupElement, SchemeMorphism_point_projective_field):
    """
    A rational point of an abelian variety over a field.

    EXAMPLES::

        sage: E = EllipticCurve([0,0,1,-1,0])
        sage: origin = E(0)
        sage: origin.domain()
        Spectrum of Rational Field
        sage: origin.codomain()
        Elliptic Curve defined by y^2 + y = x^3 - x over Rational Field
    """
    pass

