Math
====

**Functions of multidimensional arguments:**

.. currentmodule:: lena.math.meshes
.. autosummary::
    flatten
    mesh
    md_map
    refine_mesh

**Functions of scalar and multidimensional arguments:**

.. currentmodule:: lena.math.utils
.. autosummary::
    clip
    isclose

**Elements:**

.. currentmodule:: lena.math.elements
.. autosummary::
    DSum
    Mean
    Sum
    Vectorize

**3-dimensional vector:**

.. currentmodule:: lena.math.vector3
.. autosummary::
    vector3

Functions of multidimensional arguments
---------------------------------------

.. module:: lena.math.meshes
.. autofunction:: flatten
.. autofunction:: mesh
.. autofunction:: md_map
.. autofunction:: refine_mesh

Functions of scalar and multidimensional arguments
--------------------------------------------------

.. module:: lena.math.utils
.. autofunction:: clip

.. _isclose_label:
.. autofunction:: isclose

Elements
--------
.. automodule:: lena.math.elements

3-dimensional vector
--------------------

.. automodule:: lena.math.vector3
    :exclude-members: vector3

.. autoclass:: vector3
    :members: 
        angle, 
        cosine, cross, 
        dot,
        from_spherical,
        isclose,
        norm,
        proj,
        scalar_proj,
        rotate
    :exclude-members:
        phi, theta,
        getphi, getr, gettheta,
        setphi, setr, settheta,
        getcostheta, getr2,
    
..    .. automethod:: from_spherical
