# op_art_generator
To get `svgwrite`, run `pip install svgwrite`
To get `cairosvg`, run `brew install cairo` then `pip install cairosvg`
cairosvg example.svg -o example.png

# Packages to install for visualiser
rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install PyQt5 PyQtWebEngine svgwrite

TODO: add numpy, cairosvg and sympy pip installs here