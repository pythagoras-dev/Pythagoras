import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pythagoras"
    ,version="0.17.2"
    ,author="Volodymyr (Vlad) Pavlov"
    ,author_email="vlpavlov@ieee.org"
    ,description= "Planet-scale distributed computing in Python."
    ,long_description=long_description
    ,long_description_content_type="text/markdown"
    ,url="https://github.com/pythagoras-dev/pythagoras"
    ,packages=["pythagoras"
        , "pythagoras._010_basic_portals"
        , "pythagoras._040_logging_code_portals"
        , "pythagoras._030_data_portals"
        , "pythagoras._020_ordinary_code_portals"
        , "pythagoras._050_safe_code_portals"
        , "pythagoras._060_autonomous_code_portals"
        , "pythagoras._080_pure_code_portals"
        , "pythagoras._080_compatibility_validators"
        , "pythagoras._090_swarming_portals"
        , "pythagoras._100_default_local_portals"
        , "pythagoras._110_top_level_API"
        , "pythagoras._800_persidict_extensions"
        , "pythagoras._810_output_manipulators"
        , "pythagoras._820_strings_signatures_converters"
        ]
    ,classifiers=[
        "Development Status :: 3 - Alpha"
        , "Intended Audience :: Developers"
        , "Intended Audience :: Science/Research"
        , "Programming Language :: Python"
        , "Programming Language :: Python :: 3"
        , "License :: OSI Approved :: MIT License"
        , "Operating System :: OS Independent"
        , "Topic :: Scientific/Engineering"
        , "Topic :: Scientific/Engineering :: Information Analysis"
        , "Topic :: Software Development :: Libraries"
        , "Topic :: Software Development :: Libraries :: Python Modules"
    ]
    ,keywords='cloud, ML, AI, serverless, distributed, parallel'
              ', machine-learning, deep-learning, pythagoras'
    ,python_requires='>=3.10'
    ,install_requires=[
        "persidict"
        , "lz4"
        , 'joblib'
        , 'numpy'
        , 'scipy'
        , 'pandas'
        , 'scikit-learn'
        , 'jsonpickle'
        , 'psutil'
        , 'boto3'
        , 'moto'
        , 'pytest'
        , 'autopep8'
        , 'torch'
        , 'keras'
        , 'tensorflow'
        , 'deepdiff'
    ]

)