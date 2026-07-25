from bppy.model.b_event import BEvent

# First bug in the constructor class

e1 = BEvent("e1")
e2 = BEvent("e2")

e1.data["x"] = 42
print(e2.data)  # Unexpectedly shows {'x': 42}



# Second bug in the _key method

# Same keys and values, but different insertion order
e1 = BEvent("move", {"x": 1, "y": 2})
e2 = BEvent("move", {"y": 2, "x": 1})

print("Are they equal?", e1 == e2)
print("Hashes:", hash(e1), hash(e2))
print("Keys:", e1._BEvent__key(), e2._BEvent__key())


