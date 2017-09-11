import versioneer
from setuptools import setup

with open('requirements.txt', 'r') as reqfile:
    requirements = [x.strip() for x in reqfile if x.strip()]

setup(
        name='molecular-workflow-repository',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        packages=['molflow','molflow.runners','molflow.static','molflow.definitions'],
        package_data = {'molflow.static':['*.yml']},
        url='http://molsim.bionano.autodesk.com',
        license='Apache 2.0',
        author='Aaron Virshup',
        author_email='aaron.virshup@autodesk.com',
        description='A curated, community-created collection of simulation workflows',
        install_requires=requirements,
        entry_points={
            'console_scripts': [
                'molflow = molflow.__main__:main'
            ]
        }
)
