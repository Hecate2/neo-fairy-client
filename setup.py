import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="neo-fairy-client",
    version="3.5.0.12",
    author="Hecate2",
    author_email="hecate2@qq.com",
    description="Test & debug your Neo3 smart contracts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hecate2/neo-fairy-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests>=2.31.0',
    ],
    python_requires='>=3.8',
)