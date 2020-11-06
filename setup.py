from setuptools import setup, find_packages


requirements = []

with open("README.rst") as f:
    readme = f.read()

setup(
    name="AIOConductor",
    version="0.1",
    description="asynchronous application orchestrator",
    long_description=readme,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Framework :: AsyncIO",
    ],
    keywords=(
        "asyncio asynchronous orchestration orchestrator conductor injector "
        "service component"
    ),
    url="https://bitbucket.org/cottonwood-tech/aioconductor/",
    author="Cottonwood Technology",
    author_email="info@cottonwood.tech",
    license="BSD",
    packages=find_packages(exclude=["tests", "tests.*"]),
    zip_safe=False,
    install_requires=requirements,
)
