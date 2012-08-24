# gen_xml.py

import getopt
import os
import re
import string
import sys
import xml.etree.ElementTree as ET
from BeautifulSoup import BeautifulSoup as BS
#
from cardinfo import CardInfoGatherer
import grab_html
import sanity
import sets
import special
import symbols
import tools
import xmltools

XML_VERSION = "1.3.2"
# this should be bumped up every time a change is made to the XML output
# (directly or indirectly), or if sanity checks were added.

# these tags can be added to a set
SET_TAGS= [
    "deck",         # preconstructed deck or special package
    "online",       # MTGO only
]

# ElementTree does not write the XML header, so we need to provide this
XML_HEADER = '<?xml version="1.0" ?>'

DEBUG = False

def gen_xml(short_set):
    ids = grab_html.read_ids(short_set)
    root = generate_base_xml(short_set)
    cards = root.find('.//cards')
    for idx, id in enumerate(ids):
        if short_set == 'UGL' and id in special.UNGLUED_TOKENS:
            print "Skipping token:", id
            continue

        print id
        sp = open_with_bs(short_set, id, 'p')
        so = open_with_bs(short_set, id, 'o')

        try:
            d = gather_data(so, id)
        except:
            print "Multiverse id:", id
            raise
        d['type_oracle'] = d['type']
        d['rules_oracle'] = d['rules']
        del d['type'], d['rules']
        d['type_printed'], d['rules_printed'] = extract_printed_data(sp, id)
        d['multiverseid'] = str(id)

        try:
            back = special.double_faced_cards[id]
        except KeyError:
            pass
        else:
            d['doublefaced'] = ('front', str(back))

        try:
            front = special.doublefaced_reverse[id]
        except KeyError:
            pass
        else:
            d['doublefaced'] = ('back', str(front))

        print d
        sanity.check_card_dict(d)

        add_xml_element(cards, d)
        if DEBUG and idx > 1: break # FIXME

    write_xml(short_set, root)
    print "Done"

ATTRS = ['name', 'manacost', 'type', 'rules',
         'rarity', 'number', 'artist', 'power', 'toughness', 
         'loyalty', 'flavor_text']
SPECIAL = ['manacost', 'doublefaced']
# these attribute names should correspond to CardInfoGatherer methods and the
# eventual XML tags that we're going to use

def generate_base_xml(short_set):
    s = sets.set_info[short_set]
    root = ET.Element('root')
    meta = ET.SubElement(root, 'meta')
    version = ET.SubElement(meta, 'version')
    version.text = XML_VERSION
    set = ET.SubElement(root, 'set')
    set_name = ET.SubElement(set, 'name')
    set_name.text = s.name
    set_shortname = ET.SubElement(set, 'shortname')
    set_shortname.text = short_set
    noc = ET.SubElement(set, 'number_of_cards')
    noc.text = str(s.cards)
    date = ET.SubElement(set, 'release_date')

    tags = ET.SubElement(set, 'tags')
    # add tags, if any
    for tag in SET_TAGS:
        if getattr(s, tag, None):
            _ = ET.SubElement(tags, tag) # value does not matter

    date.text = s.date
    cards = ET.SubElement(set, 'cards')
    return root

def gather_data(soup, id):
    d = {}
    cig = CardInfoGatherer(soup, id)
    for attr in ATTRS:
        value = getattr(cig, attr)()
        if value is not None:
            d[attr] = value

    return d

def extract_printed_data(soup, id):
    cig = CardInfoGatherer(soup, id)
    return cig.type(), cig.rules()

def open_with_bs(short_set, id, suffix):
    path = os.path.join('html', short_set, "%s-%s.html" % (id, suffix))
    with open(path, 'rb') as f:
        data = f.read()
    return BS(data)

def add_xml_element(elem, d):
    card = ET.SubElement(elem, 'card')

    for key, value in d.items():
        if key in SPECIAL: continue
        x = ET.SubElement(card, key)
        x.text = value

    manacost = ET.SubElement(card, 'manacost')
    for symbol in d['manacost']:
        s = ET.SubElement(manacost, 'symbol')
        s.text = symbol

    # add double-faced indicator
    try:
        side, counterpart = d['doublefaced']
    except KeyError:
        pass
    else:
        dblfaced = ET.SubElement(card, 'doublefaced')
        sidenode = ET.SubElement(dblfaced, 'side')
        sidenode.text = side
        cntrnode = ET.SubElement(dblfaced, 'other')
        cntrnode.text = counterpart

    return card

def write_xml(short_set, root):
    if not os.path.exists('xml'): os.makedirs('xml')
    print "Writing XML..."
    path = os.path.join('xml', short_set + ".xml")
    with open(path, 'wb') as f:
        f.write(XML_HEADER + "\n")
        xmltools.pprint_xml(root, f=f)

    sanity.validate_xml(path)

re_version = re.compile("<version>(.*?)</version>")

def find_updates():
    """ Return the sets whose XML files needs updated, i.e. they have a
        version < the latest version. """
    behind = []
    for short_set in sets.set_info.keys():
        path = os.path.join("xml", short_set + ".xml")
        with open(path, 'rb') as f:
            chunk = f.read(2048) # read first 2K
        m = re_version.search(chunk)
        if m:
            file_version = m.group(1)
            if file_version < XML_VERSION:
                behind.append(short_set)
        else:
            # no version?! must be really old
            behind.append(short_set)

    return behind


if __name__ == "__main__":

    opts, args = getopt.getopt(sys.argv[1:], "du", ["update"])
    if args == ["all"]:
        args = sorted(sets.set_info.keys())

    for o, a in opts:
        if o == '-d':
            print "Running in debug mode"
            DEBUG = True
        elif o in ("--update", "-u"):
            args = find_updates()
            print "Updating:", args

    for short_set in args:
        gen_xml(short_set)

