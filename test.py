



def is_factorable_mod_m(m):
    """Return True if n^2 + 3n + 1 ≡ 0 (mod m) has an integer solution."""
    for n in range(m):
        if (n**2 + 3*n + 1) % m == 0:
            return True
    return False

factorable_moduli = [m for m in range(2, 501) if is_factorable_mod_m(m)]

print("Moduli (up to 500) where n^2 + 3n + 1 is factorable:")
print(factorable_moduli)
print(f"Count: {len(factorable_moduli)}")
