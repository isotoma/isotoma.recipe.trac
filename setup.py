from setuptools import setup, find_packages

version = '0.0.9'

setup(
    name = 'isotoma.recipe.trac',
    version = version,
    description = "Buildout recipes to install and configure a Trac instance",
    long_description = open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
    url = "http://pypi.python.org/pypi/isotoma.recipe.trac",
    classifiers = [
        "Framework :: Buildout",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords = "Trac subversion",
    author = "Tom Wardill",
    author_email = "tom.wardill@isotoma.com",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    package_data = {
        '': ['README.rst', 'CHANGES.txt'],
        #'isotoma.recipe.pound': ['pound.cfg', 'apache.conf']
    },
    namespace_packages = ['isotoma', 'isotoma.recipe'],
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'zc.buildout',
        'Cheetah',
        'isotoma.recipe.gocaptain',
        'zc.recipe.egg',
        'Trac >= 0.12',
    ],
    entry_points = {
        "zc.buildout": [
            "default = isotoma.recipe.trac:Recipe",
        ],
    }
)
