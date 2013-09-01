import subprocess
from sets import set_info
from scan_set import write_ids, scan_set
from grab_html import grab_html
from gen_xml import gen_xml

set_short_codes = sorted(s for s in set_info.keys())

# scan cards
for code in set_short_codes:
    ids = scan_set(code)
    write_ids(code, ids)

# grab html
for code in set_short_codes:
    grab_html(code)

# write xml
for code in set_short_codes:

    gen_xml(code)