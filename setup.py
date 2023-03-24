from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in payment_gateway_bidvest/__init__.py
from payment_gateway_bidvest import __version__ as version

setup(
	name="payment_gateway_bidvest",
	version=version,
	description="Bidvest Payment Gateway Intergration",
	author="Nigel Jena",
	author_email="hypej.10@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
