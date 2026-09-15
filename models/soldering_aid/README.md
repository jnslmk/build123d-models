# SP16-compatible / SP17 soldering aid

One thin-wall L-profile extrusion holds two threaded circular connectors while
soldering. The lower leg and rear wall are 2 mm thick; the rear wall is 60 mm
high, with the seats near its upper side ends. The threaded bosses project from
the front of the wall so connectors screw in horizontally.

The two seats are intentionally different:

- left: generic SP16-compatible, **M16 × 1.5** (verify the seller's drawing)
- right: WEIPU SP17, **M17 × 1** (SP1712 panel connector)

The model uses 0.30 mm diametral female-thread clearance as a PETG baseline and
8 mm of printed thread engagement. Print one test before committing a connector
pair: generic SP16 listings vary, while WEIPU's official SP17 family is the
documented match for the right-hand seat.

The bosses use a chamfered thread entrance. The clean L-profile has a 0.35 mm
bed/top chamfer and 0.8 mm fillets on its vertical outer edges.

## WEIPU designation note

WEIPU's official product page identifies **SP17** as the threaded-coupling
family and lists SP1710, SP1711C, SP1712 and SP1715 variants. Its SP1712
drawing specifies **M17 × 1**, a Ø17 panel cutout, a 15.6 mm anti-rotation
flat, and 3 mm maximum panel thickness.

The similarly named **SA16** is a different official WEIPU family: push-pull
coupling, not a threaded SP16 family. No official WEIPU SP16 threaded family
was found, so the left seat is explicitly treated as a generic SP16-compatible
M16 × 1.5 assumption rather than a WEIPU-certified dimension.

## Sources

- [WEIPU SP17 product page](https://www.weipuconnector.com/products/sp17/)
- [WEIPU SP1712 dimensional drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1712-2D-scaled.png)
- [WEIPU SP17 specification image](https://www.weipuconnector.com/wp-content/uploads/2023/11/WEIPU-SP17-spec.png)
- [WEIPU SA16 product page](https://www.weipuconnector.com/products/sa16/)
- Research note: `docs/research-weipu-sp16-sp17.md`
