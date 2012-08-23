# sanity.py
# Sanity checks for card data and such.

import re
import xml.etree.ElementTree as ET
import special

re_html_entity = re.compile("&\S+;")

def check_high_ascii(s):
    for idx, c in enumerate(s):
        if ord(c) > 127:
            raise ValueError("High ASCII in string at position %d: %r" % (
                  idx, s))

def check_entities(s):
    if re_html_entity.search(s):
        raise ValueError("HTML entity in string: %r" % s)

def check_card_dict(d):
    for value in d.values():
        if isinstance(value, basestring):
            check_high_ascii(value)
            check_entities(value)

    assert d.has_key('type_printed')
    assert d.has_key('type_oracle')
    assert d.has_key('name')

    if 'planeswalker' in d['type_oracle'].lower() \
    and int(d['multiverseid']) not in special.double_faced_cards.values():
        assert d.has_key('loyalty'), d

    # applies to creatures, but not to "enchant creature" cards (like in
    # Unglued, whose cards haven't been updated by the "oracle")
    if 'creature' in d['type_oracle'].lower() \
    and 'enchant ' not in d['type_oracle'].lower():
        assert d.has_key('power')
        assert d.has_key('toughness')

def validate_xml(path):
    ET.parse(path) # should not raise an error

