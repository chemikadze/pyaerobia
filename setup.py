from distutils.core import setup

setup(
    name='pyaerobia',
    description='aerobia.ru unofficial client',
    version='0.1',

    py_modules=['pyaerobia'],
    package_dir={'': 'src'},
    packages=[''],
    requires=['beautifulsoup4', 'requests', 'wsgiref'],

    author='Nikolay Sokolov',
    author_email='chemikadze@gmail.com',
    url='https://github.com/chemikadze/pyaerobia',
)
