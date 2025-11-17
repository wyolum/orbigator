include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>

N = 60 * 2;
n = 7 * 2;
pitch = 2;

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;

h = 8;

translate([R,0,0])
spur_gear(circ_pitch=pitch, teeth=n, thickness=h, shaft_diam=5.3,
	  herringbone=true, helical=-30);

ring_gear(circ_pitch=pitch,teeth=N,thickness=h,
	  herringbone=true, helical=30);
