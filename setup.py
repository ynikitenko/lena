import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lena",
    version="0.1",
    author="Yaroslav Nikitenko",
    author_email="metst13@gmail.com",
    description="Lena is an architectural framework for data analysis",
    long_description=long_description,
    long_description_content_type="text/rst",
    url="https://github.com/ynikitenko/lena",
    packages=["lena"],
    # packages=setuptools.find_packages(),
    classifiers=[
        # "Development Status :: 4 - Beta",
        "Development Status :: 3 - Alpha",
        "Environment :: Console", 
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)
