"""Mascot mapping and optional phobia filter groups."""
# Same optional list-filter behavior as the DS3 trainer.
PHOBIA_GROUPS = frozenset(str(group) for group in (
    107,201,202,203,204,205,206,209,210,214,220,222,223,224,226,227,662,672,
))

# Editorial shortlist from recurring complaints across linked community threads.
# Whole catalog families are shown; this is not a popularity ranking.
ANNOYING_GROUPS = frozenset(str(group) for group in (
    105,131,124,125,209,227,301,306,319,331,313,601,661,662,
))

def category_matches(group, phobia=False, annoying=False):
    # Category checkboxes form a union; search/region are additional constraints.
    return (not phobia and not annoying) or (phobia and group in PHOBIA_GROUPS) or (annoying and group in ANNOYING_GROUPS)

# Illustrative species symbols, not exact DS2 character portraits.
ICONS = {
    100:16,101:16,102:8,103:8,105:9,106:48,107:47,108:13,
    113:45,115:8,117:38,118:35,121:28,123:54,124:8,125:47,
    127:13,129:42,131:22,132:10,133:58,134:14,135:50,
    138:33,139:8,141:46,146:12,147:13,148:12,149:14,
    150:24,151:24,152:21,153:22,155:46,157:10,
    201:1,202:1,203:32,204:18,205:60,206:43,209:5,210:0,
    213:31,214:1,216:57,217:54,220:60,222:0,223:6,
    224:54,226:6,227:17,300:28,301:22,302:33,306:21,
    308:16,309:28,311:50,312:26,313:20,314:24,315:24,
    316:35,317:19,319:21,321:30,330:8,331:19,337:8,
    509:35,511:22,512:36,601:56,650:59,651:35,653:26,
    654:62,656:59,657:14,659:38,660:25,661:17,662:6,
    663:25,665:22,666:22,670:9,671:38,672:60,674:42,
    677:13,683:19,689:21,880:22,
}
