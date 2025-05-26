# coding: future-tstrings
dude = "10"
duded = "1010"
print({k: v for k, v in globals().items() if not k.startswith("_")})

# print((t"""hello {dude} world"""))
