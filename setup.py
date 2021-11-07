import setuptools


with open("README.rst", "r") as readme:
    long_description = readme.read()


setuptools.setup(
    name="lena",
    version="0.4",
    author="Yaroslav Nikitenko",
    author_email="metst13@gmail.com",
    description="Lena is an architectural framework for data analysis",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/ynikitenko/lena",
    project_urls = {
        'Documentation': "https://lena.readthedocs.io",
        'Source': 'https://github.com/ynikitenko/lena',
        'Tracker': 'https://github.com/ynikitenko/lena/issues',
    },
    keywords="data analysis framework",
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console", 
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)
