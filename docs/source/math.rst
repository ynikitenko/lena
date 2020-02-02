math package
============

Functions of multidimensional arguments
---------------------------------------

.. module:: lena.math.meshes
.. autofunction:: mesh
.. autofunction:: md_map

Functions of scalar and multidimensional arguments
--------------------------------------------------

.. module:: lena.math.utils
.. autofunction:: clip

.. _isclose_label:
.. autofunction:: isclose

3-dimensional vector
--------------------

.. automodule:: lena.math.vector3
    :exclude-members: vector3

.. autoclass:: vector3
    :members: 
        angle, 
        cosine, cross, 
        dot,
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
    
    .. automethod:: fromspherical
