from setuptools import setup, find_packages
setup(
    name="piaware-configurator",
    version="7.0",
    description="Flask endpoint to configure piaware over HTTP",
    url="",
    author="Eric Tran",
    author_email="eric.tran@flightaware.com",
    license="MIT",
    packages=find_packages(),
    install_requires=["tohil", "flask", "gunicorn"],
    zip_safe=False,
)
