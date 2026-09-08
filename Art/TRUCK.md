# Roomier ice cream truck

Use `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend` as the shared master. Collection `B • Ice cream truck` contains the revised truck and fitted equipment. `Art/Exports/IceCreamTruck.glb` contains that asset alone.

The truck body is approximately 12% longer and 40% wider than the first pass. The body width is about 4 meters, with a higher ceiling. The 12-tub counter and waffle station sit against the opposite wall from the serving window. The prep equipment keeps its original working scale.

The serving opening is about 3.45 meters wide and 1.49 meters tall, with a mint frame, an outside ledge, and an opening hatch. The working aisle has more than 2.15 meters of clear width above the wheel boxes at the measured stations. All truck wordmarks and both prep-counter wordmarks have been removed. The windshield has no wiper blades or arms.

The truck faces local -X. Local -Y is the left side when facing forward and is now the driver side. Its floor is approximately 0.56 meters above the ground.

- `DriverDoor_HINGE`: local Z, 0 degrees closed, -68 degrees open.
- `PassengerDoor_HINGE`: local Z, 0 degrees closed, +68 degrees open.
- `RearEntryDoor_HINGE`: local Z, 0 degrees closed, -95 degrees open.
- `ServingHatch_HINGE`: local X, 0 degrees closed, -98 degrees open.
- Wheel roots ending in `_Wheel_AXLE` rotate around local Y.
- `InteriorEquipment_ROOT` moves the installed equipment.
- `Roof_ROOT • hide for interior view` groups the removable cargo roof and sign.
- `ServeCustomer_SOCKET` and `ServingView_SOCKET` mark service positions.

`Truck_Left_Hand_Drive.png` shows the current cabin controls. `Truck_Menu_Removed.png` shows the serving side without the menu panel. Previews `Truck_05` through `Truck_08` predate these changes. The master keeps the roof visible and the hatch open. Studio lights are excluded from exports.

Checks include nine unobstructed rays through the serving window, three cross-aisle clearance checks, and removal of the counter lettering vertices. Results are in `Art/Source/truck-space-verification.json`. There are no colliders, vehicle physics, movement, or interaction scripts yet.

`Art/Source/build_roomier_truck.py` builds the revised truck source using the preserved prep snapshot. `revise_workshop.py` installs it and simplifies decorative equipment geometry. Preserve manual edits before rebuilding. The earlier builder creates the superseded truck.

The small three-cone menu panel beside the serving opening has been removed from the master, truck copies, exports, and source builder. `Source/menu-removal-verification.json` records the removal of its 11 components and 255 source vertices per file.

The wheel, steering column, instrument gauges, dashboard switches, gear lever, pedals, and driver placement anchors use the left-hand layout. Both seats remain in the cab. Door and road-wheel names now match their physical left and right sides. `Source/left_hand_drive.py` applies the same arrangement in future builds; the saved-model checks are in `Source/left-hand-drive-verification.json`. Geometry counts are unchanged and mesh normals were reflected with the geometry, with no negative object scales.
