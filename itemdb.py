from dataclasses import dataclass
from typing import Protocol, TypeVar, Generic

class _SupportsRead(Protocol):
    def read(self, size: int) -> bytes:
        ...

@dataclass(frozen=True)
class _Field:
    """ Used for defining Item template fields. Size represents the number of bytes to read from the buffer, but
    the default value -1 represents dynamic size (used in strings). Version represents the version of the ItemDB
    when the field was added, and xor_key is used when a string is XORred (e.g. item names). """
    size:    int = -1
    version: int = 1
    xor_key: str | None = None

@dataclass
class Item:
    """ This is the default Item template. You can create your own template by creating a dataclass and using _Fields,
    and then pass the template to the itemdb_read function. However, ideally, this template should be up-to-date with 
    the latest version of the ItemDB and should be perfectly fine for most use cases. 
    
    Annotation is used to denote whether the field should be interpreted Python-side as an integer or a string, or if
    the field is unknown or we want to ignore it for some reason, we may set it to None.
    """
    id:             int  = _Field(size=4)
    properties:     int  = _Field(size=2)
    type:           int  = _Field(size=1)
    material:       int  = _Field(size=1)
    name:           str  = _Field(xor_key="PBG892FXX982ABC*")
    file_name:      str  = _Field()
    file_hash:      int  = _Field(size=4)
    visual_type:    int  = _Field(size=1)
    cook_time:      int  = _Field(size=4)
    tex_x:          int  = _Field(size=1)
    tex_y:          int  = _Field(size=1)
    storage_type:   int  = _Field(size=1)
    layer:          int  = _Field(size=1)
    collision_type: int  = _Field(size=1)
    hardness:       int  = _Field(size=1)
    regen_time:     int  = _Field(size=4)
    clothing_type:  int  = _Field(size=1)
    rarity:         int  = _Field(size=2)
    max_hold:       int  = _Field(size=1)
    alt_file_path:  str  = _Field()
    alt_file_hash:  int  = _Field(size=4)
    anim_ms:        int  = _Field(size=4)
    pet_name:       str  = _Field(version=4)
    pet_prefix:     str  = _Field(version=4)
    pet_suffix:     str  = _Field(version=4)
    pet_ability:    str  = _Field(version=5)
    seed_base:      int  = _Field(size=1)
    seed_over:      int  = _Field(size=1)
    tree_base:      int  = _Field(size=1)
    tree_over:      int  = _Field(size=1)
    bg_col:         int  = _Field(size=4)
    fg_col:         int  = _Field(size=4)
    seed1:          int  = _Field(size=2)
    seed2:          int  = _Field(size=2)
    bloom_time:     int  = _Field(size=4)
    anim_type:      int  = _Field(size=4, version=7)
    anim_string:    str  = _Field(version=7)
    anim_tex:       str  = _Field(version=8)
    anim_string2:   str  = _Field(version=8)
    dlayer1:        int  = _Field(size=4, version=8)
    dlayer2:        int  = _Field(size=4, version=8)
    properties2:    int  = _Field(size=2, version=9)
    _unknown1:      None = _Field(size=62, version=9)
    tile_range:     int  = _Field(size=4, version=10)
    pile_range:     int  = _Field(size=4, version=10)
    custom_punch:   str  = _Field(version=11)
    _unknown2:      None = _Field(size=13, version=12)
    clock_div:      int  = _Field(size=4, version=13)
    parent_id:      int  = _Field(size=4, version=14)
    _unknown3:      None = _Field(size=25, version=15)
    alt_sit_path:   str  = _Field(version=15)
    _unknown4:      str  = _Field(version=16)


def _parse_int(buffer: _SupportsRead, size: int) -> int:
    return int.from_bytes(buffer.read(size), "little")

def _parse_str(buffer: _SupportsRead) -> str:
    len = _parse_int(buffer, 2)
    return buffer.read(len).decode("utf-8")

def _xor_str(str: str, key: str, offset: int):
    result = ""
    for i in range(len(str)):
        result += chr(ord(str[i]) ^ ord(key[(i + offset) % len(key)]))
    return result

T = TypeVar("T")
def parse(buffer: _SupportsRead, template: T = Item) -> tuple[int, int, list[T]]:
    """ Reads ItemDB from buffer and returns a tuple containing the version, item count, and a list of items.
    The list of items consists of class instances of the template argument type. If a field is None, its
    either unknown or not present in your ItemDB version. """
    version = _parse_int(buffer, 2)
    item_count = _parse_int(buffer, 4)
    items = []
    for i in range(item_count):
        item = template()
        for k, t in template.__annotations__.items():
            f: _Field = getattr(item, k)
            value = None
            if f.version > version:
                pass
            elif t == int:
                value = _parse_int(buffer, f.size)
            elif t == str:
                value = _parse_str(buffer)
                if f.xor_key is not None and version >= 3:
                    value = _xor_str(value, f.xor_key, i)
            elif t is None:
                _parse_int(buffer, f.size) if f.size > 0 else _parse_str(buffer)
            else:
                raise ValueError(f"Unknown field type in template: {k} = {t.__name__}")
            setattr(item, k, value)
        if i != item.id:
            raise ValueError(f"Offset mismatch, template is likely out-of-date ({i} != {item.id}, v{version})")
        items.append(item)
    return version, item_count, items

if __name__ == "__main__":
    # Usage: python itemdb.py [input path] [output path]
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "items.dat"
    out = open(sys.argv[2] if len(sys.argv) > 2 else "items.txt", "w")
    version, item_count, items = parse(open(path, "rb"))
    first = items[0]
    # Valid keys are those which values are not None. If a value is None, that means
    # the field is either unknown or not present in the version of the file being parsed.
    valid_keys = [k for k in first.__dict__.keys() if first.__dict__[k] is not None]
    out.write("|".join(map(str, valid_keys)) + "\n")
    for i in items:
        out.write("|".join(map(
            lambda k: f'"{str(getattr(i, k))}"' if isinstance(getattr(i,k), str) else str(getattr(i, k)), 
            valid_keys
        )) + "\n")
    print(f"Successfully parsed {item_count} items from ItemDB v{version} and wrote to {out.name}")
