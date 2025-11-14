"""
Database of common molecular geometries (optimized structures)
"""

# Geometries in Angstroms: (element, (x, y, z))
MOLECULAR_GEOMETRIES = {
    'H2O': [
        ('O', (0.0, 0.0, 0.0)),
        ('H', (0.757, 0.586, 0.0)),
        ('H', (-0.757, 0.586, 0.0))
    ],
    'CH4': [
        ('C', (0.0, 0.0, 0.0)),
        ('H', (0.629, 0.629, 0.629)),
        ('H', (-0.629, -0.629, 0.629)),
        ('H', (-0.629, 0.629, -0.629)),
        ('H', (0.629, -0.629, -0.629))
    ],
    'NH3': [
        ('N', (0.0, 0.0, 0.0)),
        ('H', (0.0, 0.938, 0.383)),
        ('H', (0.812, -0.469, 0.383)),
        ('H', (-0.812, -0.469, 0.383))
    ],
    'CO2': [
        ('C', (0.0, 0.0, 0.0)),
        ('O', (1.16, 0.0, 0.0)),
        ('O', (-1.16, 0.0, 0.0))
    ],
    'O2': [
        ('O', (0.0, 0.0, 0.0)),
        ('O', (1.21, 0.0, 0.0))
    ],
    'N2': [
        ('N', (0.0, 0.0, 0.0)),
        ('N', (1.10, 0.0, 0.0))
    ],
    'H2': [
        ('H', (0.0, 0.0, 0.0)),
        ('H', (0.74, 0.0, 0.0))
    ],
    'C2H5OH': [  # Ethanol
        ('C', (0.0, 0.0, 0.0)),
        ('C', (1.52, 0.0, 0.0)),
        ('O', (2.02, 1.35, 0.0)),
        ('H', (2.98, 1.35, 0.0)),
        ('H', (-0.38, -0.52, 0.89)),
        ('H', (-0.38, -0.52, -0.89)),
        ('H', (-0.38, 1.03, 0.0)),
        ('H', (1.90, -0.52, 0.89)),
        ('H', (1.90, -0.52, -0.89))
    ],
    'NaCl': [
        ('Na', (0.0, 0.0, 0.0)),
        ('Cl', (2.36, 0.0, 0.0))
    ]
}

def get_molecule_geometry(formula: str):
    """Get optimized geometry for a molecule"""
    return MOLECULAR_GEOMETRIES.get(formula, None)

def parse_molecular_formula(formula: str):
    """Parse formula like H2O into list of elements"""
    import re
    pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
    elements = []
    for match in pattern.finditer(formula):
        elem = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        elements.extend([elem] * count)
    return elements
