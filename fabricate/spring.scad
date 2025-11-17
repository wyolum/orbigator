//https://www.lowes.com/pd/Hillman-2-Pack-2-in-Zinc-Plated-Steel-Window-Screen-Tension-Springs/3925333

inch = 25.4;

D = 3 * inch / 8;

d = .9;

// Torus module
module torus(R, r) {
  rotate_extrude(angle = 360, $fn=100)
        translate([R, 0, 0])
            circle(r = r);
}

// Helix along +X with flat, gap-free ends.
// OD: outer diameter of the coil (includes wire), same units as your scene
// thickness: wire diameter
// pitch: advance per full turn (distance along X for 360°)
// n_coil: number of turns
module slow_helix(OD, thickness, pitch, n_coil) {
    r = thickness/2;
    R = OD/2 - r;                 // path radius to tube center
    L = pitch * n_coil;           // total length along X
    assert(R > 0, "OD must be greater than thickness");

    overshoot = 2 * r;            // extra to trim for perfectly flat ends

    intersection() {
        // Build an oversized helix, then clip to [0, L] for flat end faces
        translate([-overshoot, 0, 0])
            rotate([0, 90, 0]) // put helix axis along X
                linear_extrude(height = L + 2*overshoot,
                               twist  = n_coil * 360,
                               slices = max(200, ceil(n_coil * 120)))
                    translate([R, 0, 0])
                        circle(r = r, $fn = 64);

        // Clipping slab: keep exactly x in [0, L]
        translate([0, -OD, -OD])
            cube([L, 2*OD, 2*OD], center = false);
    }
}

module ring_stack(D, d, n){
  for(i=[0:n-1]){
    translate([0, 0, d])torus(D, d);
  }
}

H = 2. * inch;
module spring(){
  translate([0, 0, -H/2-(D+d)/2]){
    translate([0, 0, (D + d) / 2])rotate([90, 0, 0])
      torus(D/2, d/2);
    
    translate([0, 0, H+(D+d)/2])rotate([90, 0, 0])
      torus(D/2, d/2);
    
    translate([0,0,D-d])
      for(i=[1:47]){
	translate([0, 0, i * d])torus(D/2, d/2);
      }
  }
}
spring();
color("red")cylinder(h=2*inch, d=D/2, center=true, $fn=30);
