# Lens cap

A shallow, push-on camera lens cap that protects a lens barrel with a closed
disc and a flexible friction-fit ring. The default 51 mm bore is for a barrel
whose measured outside diameter is 51 mm; set `inner_dia` to the barrel's
measured diameter when using the parametric model.

The cap intentionally adds no clearance to that measurement: an FDM bore prints
slightly undersize and the thin wall flexes onto the barrel. If a printed cap is
too tight, increase `inner_dia` in 0.2 mm steps rather than thinning the wall.
Print in PETG with the closed face down and open mouth up. It needs no supports.

## Design decisions

- The default 1.2 mm wall is three 0.4 mm perimeters, thin enough to flex for
  friction retention rather than hoop-stress against the barrel.
- The closed disc is the bed-facing first layer, avoiding a bridge across the
  cavity and providing elephant-foot relief at that edge.
- The open mouth has chamfers on both its bore and outside edges, so it leads
  onto the barrel without leaving a knife-edge rim.
