# gt-itemdb-parser
Easy-to-use tool and library to parse Growtopia's items.dat file, written in Python 3.08. 

### Usage as a tool
If you're a casual user, using the tool is straight-forward:\
`python itemdb.py [items.dat path] [output path]`\
These arguments are optional and if omitted the tool will fallback to its current working directory.

### Basic usage as a library
The module exports a single function called `parse`:
```python
import itemdb
version, item_count, items = itemdb.parse(open("items.dat", "rb"))
print("items.dat version is", version, "and item count is", item_count)
print("list of items with donation box type:")
for item in items:
    if item.type == 47:
        print(item.name)
```

### Advanced usage as a library
If for some reason the tool is out-of-date or you only care about storing certain data about items, you might want to create your own Item template that you can pass to the `parse` function. To do this, you may want to take a look at the source code and how the `Item` and `_Field` dataclasses are implemented, but here's the gist of it:
- `_Field.size` represents the amount of bytes to read, but it may be -1 in case of strings (dynamic size).
- `_Field.version` is the first version that the field has appeared in. If `parse` is parsing an ItemDB where the version is smaller than this value, the field will be set to None.
- `_Field.xor_key` is as of now only used for decrypting item names, just copy it over from the default `Item` class implementation.

A mock template class would look something like this:
```python
@dataclass
class MockItem:
    some_number: int = _Field(size=4, version=1)
    some_encrypted_text: str = _Field(version=1, xor_key="lol")
    some_value_to_ignore: None = _Field(size=123)
    some_text_to_ignore: None = _Field()
```
Basically, type annotations are used to describe how Python should interpret the value, and the default `_Field` values tell the `parse` function how to read the field. Your custom template can be passed to the `parse` function via optional `template` argument. 

More detailed explanations are present inside the source code.

### Contributing
If you know what any of the `_unknownX` fields represent in the items.dat file format, feel free to reach out.
