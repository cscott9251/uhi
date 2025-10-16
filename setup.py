from setuptools import setup, find_packages

setup(
   name='UHI',
   version='1.0',
   description='A useful module',
   author='Man Foo',
   author_email='foomail@foo.example',
   packages=find_packages(where='src'),
   package_dir={'': 'src'},
   install_requires=["geopandas","numpy","shapely"]
)