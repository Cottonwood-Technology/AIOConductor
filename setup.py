from setuptools import setup, find_packages


requirements = []

with open("README.rst") as f:
    readme = f.read()

with open("aioconductor/__init__.py") as f:
    version = next(line for line in f if line.startswith("__version__"))
    version = version.strip().split(" = ")[1]
    version = version.strip('"')

setup(
    name="AIOConductor",
    version=version,
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
    url="https://github.com/Cottonwood-Technology/AIOConductor",
    author="Cottonwood Technology",
    author_email="info@cottonwood.tech",
    license="BSD",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"aioconductor": ["py.typed"]},
    zip_safe=False,
    install_requires=requirements,
)
