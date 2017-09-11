import versioneer
from setuptools import setup

setup(
        name='molecular-workflow-repository',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        packages=['molflow'],
        url='http://molsim.bionano.autodesk.com',
        license='Apache 2.0',
        author='Aaron Virshup',
        author_email='aaron.virshup@autodesk.com',
        description='A curated, community-created collection of simulation workflows',
        entry_points={
            'console_scripts': [
                'molflow = molflow.__main__:main'
            ]
        }
)
