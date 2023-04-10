"""*vector3* is a 3-dimensional vector.
It supports spherical and cylindrical coordinates
and basic vector operations.

Initialization, vector addition and scalar multiplication
create new vectors:

>>> v1 = vector3(0, 1, 2)
>>> v2 = vector3(3, 4, 5)
>>> v1 + v2
vector3(3, 5, 7)
>>> v1 - v2
vector3(-3, -3, -3)
>>> 3 * v1
vector3(0, 3, 6)
>>> v1 * 3
vector3(0, 3, 6)

Vector attributes can be set and read.
Vectors can be tested for exact or approximate equality
with `==` and :meth:`isclose <vector3.isclose>` method.

>>> v2.z = 0
>>> v2
vector3(3, 4, 0)
>>> v2.r = 10
>>> v2 == vector3(6, 8, 0)
True
>>> v2.theta = 0
>>> v2.isclose(vector3(0, 0, 10))
True
>>> from math import pi
>>> v2.phi = 0
>>> v2.theta = pi/2.
>>> v2.isclose(vector3(10, 0, 0))
True

Vector components are floats in general.
Other values can be used as well,
if that makes sense for the operations used
(types are not tested during the initialization).
For example, vectors in the examples above have integer coordinates,
which will become floats if we multiply them by floats,
divide or maybe rotate.
For usual vector additions or subtractions, though,
their coordinates will remain integer.
"""

from math import sin, cos, acos, pi, atan2, sqrt

import lena.core
import lena.math

# pylint: disable=invalid-name,too-many-public-methods
## vector3 has semantics of a simple type (compared to Lena elements),
## hence its name is lowercase;
## and it has many public methods because of rich allowed operations.


class vector3(object):
    """3-dimensional vector with Cartesian, spherical
    and cylindrical coordinates.
    """

    def __init__(self, x, y, z):
        r"""Create a vector from Cartesian coordinates *x*, *y*, *z*.

        **Attributes**

        *vector3* has usual vector attributes *x*, *y*, *z*,
        spherical coordinates *r*, *phi*, *theta*
        and cylindrical ones *rho* and *rho2* (*rho^2 = x^2 + y^2*).

        Spherical and Cartesian coordinates are connected
        by this formula:

        .. math::
           :nowrap:

           \begin{gather*}
           \begin{aligned}
               x & = r * \cos(\phi) * \sin(\theta),\\
               y & = r * \sin(\phi) * \sin(\theta),\\
               z & = r * \cos(\theta),\\
           \end{aligned}
           \end{gather*}

        :math:`\phi \in [0, 2 \pi], \theta \in [0, \pi]`.

        :math:`\phi` and :math:`\phi + 2 \pi` are equal.

        Cartesian coordinates can be obtained and set through indices
        starting from 0 (v.x = v[0]).
        In this respect, *vector3* behaves as a container of length 3.

        Only Cartesian coordinates are stored internally
        (spherical and other coordinates are recomputed each time).

        Attributes can be got and set using subscript
        or a function set*, get*.
        For example:

        >>> v = vector3(1, 0, 0)
        >>> v.x = 0
        >>> x = v.getx()
        >>> v.setx(x+1)
        >>> v
        vector3(1, 0, 0)

        :math:`r^2` and :math:`\cos\theta` can be obtained
        with methods *getr2()* and *getcostheta()*.

        **Comparisons**

        For elementwise comparison of two vectors
        one can use '==' and '!=' operators.
        Because of rounding errors, this can often show
        two same vectors as different.
        In general, it is recommended to use approximate comparison with
        :meth:`isclose <vector3.isclose>` method.

        Comparisons like '>', '<=' are all prohibited:
        if one tries to use these operators,
        :exc:`.LenaTypeError` is raised.

        **Truth testing**

        *vector3* is non-zero if its magnitude (*r*) is not 0.

        **Vector operations**

        3-dimensional vectors can be added and subtracted,
        multiplied or divided by a scalar.
        Multiplication by a scalar can be written
        from any side of the vector (c*v or v*c).
        A vector can also be negated (*-v*).

        For other vector operations see methods below.
        """
        # x, y and z have no defaults, because that is more explicit
        self._v = [x, y, z]
        # self._v = list(map(float, v))

    # todo: add fromcylindrical?
    # make set_ and get_ functions private. What's the use of them?

    @classmethod
    def from_spherical(cls, r, phi, theta):
        r"""Construct a new *vector3* from spherical coordinates.

        *r* is its magnitude, *phi* is the azimuth angle
        from 0 to :math:`2 * \pi` and *theta* is the polar angle
        from 0 (z = 1) to :math:`\pi` (z = -1).

        >>> from math import pi
        >>> vector3.from_spherical(1, 0, 0)
        vector3(0.0, 0.0, 1.0)
        >>> vector3.from_spherical(1, 0, pi).isclose(vector3(0, 0, -1))
        True
        >>> vector3(1, 0, 0).isclose(vector3.from_spherical(1, 0, pi/2))
        True
        >>> vector3.from_spherical(1, pi, 0).isclose(vector3(0.0, 0.0, 1.0))
        True
        >>> vector3.from_spherical(1, pi/2, pi/2).isclose(vector3(0.0, 1.0, 0.0))
        True

        .. versionchanged:: 0.6
            Renamed from *fromspherical*.
        """
        x = r * cos(phi) * sin(theta)
        y = r * sin(phi) * sin(theta)
        z = r * cos(theta)
        return cls(x, y, z)

    ### Properties ###

    def getx(self):
        return self._v[0]

    def gety(self):
        return self._v[1]

    def getz(self):
        return self._v[2]

    def getrho(self):
        return sqrt(self._v[0]**2 + self._v[1]**2)

    def getrho2(self):
        return self._v[0]**2 + self._v[1]**2


    def setx(self, value):
        self._v[0] = value

    def sety(self, value):
        self._v[1] = value

    def setz(self, value):
        self._v[2] = value

    def setrho(self, value):
        scale = value / self.getrho()
        self._v[0] *= scale
        self._v[1] *= scale

    def setrho2(self, value):
        scale = value / self.getrho2()
        self._v[0] *= sqrt(scale)
        self._v[1] *= sqrt(scale)

    x = property(getx, setx)
    y = property(gety, sety)
    z = property(getz, setz)
    rho = property(getrho, setrho)
    rho2 = property(getrho2, setrho2)

    def getr(self):
        return self._mag()

    def getphi(self):
        """Get azimuth vector. 0 <= Phi < 2 pi.

        >>> from math import pi
        >>> from lena.math import isclose
        >>> v3 = vector3.from_spherical(1, pi/2, pi/2)
        >>> isclose(v3.getphi(), pi/2)
        True
        >>> v3.isclose(vector3(0, 1, 0))
        True
        >>> v3 = vector3.from_spherical(1, 3 * pi/2, pi/2)
        >>> isclose(v3.getphi(), 3 * pi/2)
        True
        >>> v3 = vector3(-1., 0, 0)
        >>> isclose(v3.getphi(), pi)
        True
        >>> v3 = vector3.from_spherical(10, 2 * pi - 1e-6, pi/2)
        >>> isclose(v3.getphi(), 2 * pi - 1e-6)
        True
        """
        phi = atan2(self.y, self.x)
        return phi if phi >= 0 else 2 * pi + phi

    def gettheta(self):
        """Get polar angle. z = r * cos(theta), 0 <= theta <= pi.

        >>> from math import pi
        >>> from lena.math import isclose
        >>> isclose(vector3.from_spherical(1, pi/2, pi/2).gettheta(), pi/2)
        True
        """
        return acos(self.getcostheta())

    def setr(self, r):
        """
        >>> v = vector3(0, 4, 3)
        >>> v.r
        5.0
        >>> v.r = 20
        >>> v.isclose(vector3(0, 16, 12))
        True
        """
        scale = r / self.r
        self._v = [el * scale for el in self._v]

    def setphi(self, phi):
        """
        >>> from math import pi
        >>> v = vector3(0, 4, 3)
        >>> v.phi = pi/2
        >>> v.isclose(vector3(0, 4, 3))
        True
        >>> v.phi = pi
        >>> v.isclose(vector3(-4, 0, 3))
        True
        >>> v.phi = 2 * pi
        >>> v.isclose(vector3(4, 0, 3))
        True
        """
        self._v = vector3.from_spherical(self.r, phi, self.theta)._v

    def settheta(self, theta):
        """Set the polar angle to theta.
        Note that when theta was 0 or pi,
        the resulting azimuth angle phi can be arbitrary.

        >>> from math import pi
        >>> v = vector3(0, 0, 1)
        >>> # This method probably should not be defined. Use at your own understanding.
        >>> v.theta = pi/2
        >>> # works fine
        >>> v = vector3(1, 0, 0)
        >>> v.theta = pi
        >>> v.isclose(vector3(0, 0, -1))
        True
        """
        self._v = vector3.from_spherical(self.r, self.phi, theta)._v

    r = property(getr, setr)
    phi = property(getphi, setphi)
    theta = property(gettheta, settheta)

    def _mag(self):
        """Magnitude of the vector.

        >>> v1 = vector3(0, 3, 4)
        >>> v1._mag()
        5.0
        """
        return sqrt(self.dot(self))

    def _mag2(self):
        """Squared magnitude of the vector.

        >>> v1 = vector3(0, 1, 2)
        >>> v1._mag2()
        5
        """
        return self.dot(self)

    # todo: probably make r2 an attribute (like rho2)
    # and why do we have a separate method _mag2?
    def getr2(self):
        return self._mag2()

    def getcostheta(self):
        """Get cosine of the polar angle.
        z = r * costheta, 0 <= theta <= pi.

        >>> from math import pi
        >>> from lena.math import isclose
        >>> isclose(vector3.from_spherical(1, pi/2, pi/2).getcostheta(), 0, abs_tol=1e-10)
        True
        """
        # return self.cosine(vector3(0, 0, 1))
        return lena.math.clip(self.z / self._mag(), (-1.0, 1.0))

    ## Rich comparison methods

    def __eq__(self, B):
        if not isinstance(B, vector3):
            # return NotImplemented if unsure about B,
            # https://stackoverflow.com/a/879005/952234
            # In this case B.__eq__ will be tried.
            return NotImplemented
        return self._v == B._v

    def __ne__(self, B):
        if not isinstance(B, vector3):
            return NotImplemented
        return self._v != B._v

    ## Prohibit comparison methods <, <=, >, >=, __cmp__

    # this method is never called. Probably remove.
    # def __cmp__(self, B):
    #     # works fine for Python 2, but __lt__, etc.
    #     # should be also implemented for Python 3.
    #     raise lena.core.LenaTypeError(
    #         "comparison is not supported for vector3"
    #     )

    def __lt__(self, B):
        raise lena.core.LenaTypeError(
            "comparison is not supported for vector3"
        )

    def __le__(self, B):
        raise lena.core.LenaTypeError(
            "comparison is not supported for vector3"
        )

    def __gt__(self, B):
        raise lena.core.LenaTypeError(
            "comparison is not supported for vector3"
        )

    def __ge__(self, B):
        raise lena.core.LenaTypeError(
            "comparison is not supported for vector3"
        )

    ## Emulating container

    def __getitem__(self, i):
        return self._v[i]

    def __setitem__(self, ind, value):
        self._v[ind] = float(value)

    def __iter__(self):
        return iter(self._v)

    def __len__(self):
        return 3

    def __repr__(self):
        v = self._v
        return "vector3({}, {}, {})".format(v[0], v[1], v[2])

    ### Basic operations ###

    def isclose(self, B, rel_tol=1e-09, abs_tol=0.0):
        """Test whether two vectors are approximately equal.

        Parameter semantics is the same as for the general
        :func:`isclose <lena.math.utils.isclose>`.

        >>> v1 = vector3(0, 1, 2)
        >>> v1.isclose(vector3(1e-11, 1, 2))
        True
        """
        # :func:`isclose`.
        # :ref:`isclose <isclose_label>`.
        dist = (self - B)._mag()
        return dist <= max(rel_tol * max(self._mag(), B._mag()), abs_tol)

    # http://www.siafoo.net/article/57
    # http://blog.teamtreehouse.com/operator-overloading-python

    def __nonzero__(self):
        # implement truth value testing and bool()
        # not used in Python 3 tests
        return self._mag2() != 0

    ## Regular Binary Operations

    def __add__(self, B):
        A = self._v
        return vector3(A[0] + B[0], A[1] + B[1], A[2] + B[2])

    def __sub__(self, B):
        return self + B * (-1)

    def __mul__(self, c):
        return c * self

    def __div__(self, c):
        """Divide self by a scalar *c* (Python 2).

        >>> v1 = vector3(0, 1, 2)
        >>> v1 / 2
        vector3(0.0, 0.5, 1.0)
        """
        # in Python 3 4/2 = 2.,
        # while in Python 2 4/2 is integer 2!
        # so there is no need to care about preserving integers:
        # they will be lost in general.
        return 1./c * self

    def __truediv__(self, c):
        """Divide self by a scalar *c* (Python 3).

        >>> v1 = vector3(0, 1, 2)
        >>> v1 / 2
        vector3(0.0, 0.5, 1.0)
        """
        return 1./c * self

    ## Reversed Binary Operations

    def __radd__(self, B):
        return self + B
        # return self + vector3(*B)

    def __rmul__(self, c):
        v = self._v
        return vector3(v[0]*c, v[1]*c, v[2]*c)

    ## Unary Operations

    def __neg__(self):
        """
        >>> v1 = vector3(0, 1, 2)
        >>> - v1
        vector3(0, -1, -2)
        """
        return self * (-1)

    ## Vector Operations
    # Cf. http://vpython.org/contents/docs/vector.html

    def angle(self, B):
        """The angle between self and *B*, in radians.

        >>> v1 = vector3(0, 3, 4)
        >>> v2 = vector3(0, 3, 4)
        >>> v1.angle(v2)
        0.0
        >>> v2 = vector3(0, -4, 3)
        >>> from math import degrees
        >>> degrees(v1.angle(v2))
        90.0
        >>> v2 = vector3(0, -30, -40)
        >>> degrees(v1.angle(v2))
        180.0
        """
        return acos(self.cosine(B))

    def cosine(self, B):
        """Cosine of the angle between self and *B*.

        >>> v1 = vector3(0, 3, 4)
        >>> v2 = vector3(0, 3, 4)
        >>> v1.cosine(v2)
        1.0
        >>> v2 = vector3(0, -4, 3)
        >>> v1.cosine(v2)
        0.0
        >>> v2 = vector3(0, -30, -40)
        >>> v1.cosine(v2)
        -1.0
        """
        return lena.math.clip(self.norm().dot(B.norm()), (-1.0, 1.0))

    def cross(self, B):
        """The cross product between self and *B*, :math:`A\\times B`.

        >>> v1 = vector3(0, 3, 4)
        >>> v2 = vector3(0, 1, 0)
        >>> v1.cross(v2)
        vector3(-4, 0, 0)
        """
        A = self._v
        return vector3(A[1] * B[2] - A[2] * B[1],
                       A[2] * B[0] - B[2] * A[0],
                       A[0] * B[1] - A[1] * B[0])

    def dot(self, B):
        "The scalar product between self and *B*, :math:`A \\cdot B`."
        A = self._v
        return A[0]*B[0] + A[1]*B[1] + A[2]*B[2]

    def proj(self, B):
        """The vector projection of self along B.

        A.proj(B) = :math:`(A \\cdot norm(B)) norm(B)`.

        >>> v1 = vector3(0, 3, 4)
        >>> v2 = vector3(0, 2, 0)
        >>> v1.proj(v2)
        vector3(0.0, 3.0, 0.0)
        """
        return self.dot(B.norm()) * B.norm()

    def scalar_proj(self, B):
        """The scalar projection of self along B.

        A.scalar_proj(B) = :math:`A \\cdot norm(B)`.

        >>> v1 = vector3(0, 3, 4)
        >>> v2 = vector3(0, 2, 0)
        >>> v1.scalar_proj(v2)
        3.0
        """
        return self.dot(B.norm())

    def norm(self):
        """:math:`A/|A|`, a unit vector in the direction of self.

        >>> v1 = vector3(0, 3, 4)
        >>> n1 = v1.norm()
        >>> v1n = vector3(0, 0.6, 0.8)
        >>> (n1 - v1n).r < 1e-6
        True
        """
        v = self._v
        mag = self._mag()
        return vector3(v[0]/mag, v[1]/mag, v[2]/mag)

    def rotate(self, theta, B):
        """Rotate self around *B* through angle *theta*.

        From the position where *B* points towards us,
        the rotation is counterclockwise (the right hand rule).

        >>> v1 = vector3(1, 1, 1)
        >>> v2 = vector3(0, 1, 0)
        >>> from math import pi
        >>> vrot = v1.rotate(pi/2, v2)
        >>> vrot.isclose(vector3(1, 1, -1))
        True
        """
        # Uses Rodrigues' rotation formula,
        # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
        k = B.norm()
        vpar = self.proj(k)
        vort = self - vpar
        vrot = vpar + cos(theta) * vort - sin(theta) * self.cross(k)
        return vrot
