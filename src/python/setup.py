from pathlib import Path
from zensols.pybuild import SetupUtil

su = SetupUtil(
    setup_path=Path(__file__).parent.absolute(),
    name="zensols.clinicamr",
    package_names=['zensols', 'resources'],
    # package_data={'': ['*.html', '*.js', '*.css', '*.map', '*.svg']},
    package_data={'': ['*.conf', '*.json', '*.yml']},
    description='Clincial Domain Abstract Meaning Representation Graphs',
    user='plandes',
    project='clinicamr',
    keywords=['tooling'],
    # has_entry_points=False,
).setup()
