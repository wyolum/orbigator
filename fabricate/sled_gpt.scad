// Twin-Bogie Sled for 6 mm balls (parametric)
// Prints upside-down: pocket lips on build plate.

$fn = 80;

// ---- Params ----
ball_d      = 6.00;
clearance   = 0.15;     // bore oversize
expose      = 2.4;      // how much ball protrudes below sled
wall        = 2.0;      // sled wall thickness
wheelbase   = 14.0;     // center-to-center spacing of balls
sled_w      = 14.0;     // sled width
sled_t      = 6.0;      // body thickness above ball equator
cap_t       = 1.8;      // cap thickness
cap_screw_d = 2.2;      // for M2 pilot
cap_off     = 5.0;      // screw offset from pocket center
lip_groove  = 0.4;      // dust groove size

bore_d = ball_d + clearance;

// ---- Helpers ----
module pocket() {
    // Cylindrical bore + spherical clearance on cap side
    translate([0,0,0])
    cylinder(d=bore_d, h=ball_d - expose + sled_t, center=false);
}

module dust_groove() {
    translate([0,0,0.15])
    rotate_extrude() translate([bore_d/2,0,0])
        square([lip_groove, lip_groove], center=false);
}

module cap_half() {
    // screw-on cap with spherical relief so it never pinches
    difference() {
        cylinder(d=bore_d + 2*wall, h=cap_t);
        // spherical recess
        translate([0,0,-(ball_d/2)])
            sphere(d=ball_d + 0.2);
        // screw holes (two)
        for (sx=[-cap_off, cap_off])
            translate([sx,0,-0.5]) cylinder(d=cap_screw_d, h=cap_t+1);
    }
}

// ---- Main ----
module sled() {
    // base slab
    difference() {
        // body
        hull() {
            translate([-wheelbase/2, 0, 0]) cube([wall*2, sled_w, sled_t], center=true);
            translate([ wheelbase/2, 0, 0]) cube([wall*2, sled_w, sled_t], center=true);
        }

        // pockets (open upward in print)
        for (x=[-wheelbase/2, wheelbase/2])
            translate([x, 0, 0]) pocket();

        // dust grooves at lip
        for (x=[-wheelbase/2, wheelbase/2])
            translate([x,0,0]) dust_groove();
    }
}

// caps as separate parts
module caps() {
    for (x=[-wheelbase/2, wheelbase/2])
        translate([x, sled_w/2 + 4, 0]) cap_half();
}

// visualize balls & exposure (preview only)
module balls_preview() {
    color("silver", 0.6)
    for (x=[-wheelbase/2, wheelbase/2])
        translate([x,0, (ball_d - expose) - ball_d/2])
            sphere(d=ball_d);
}

translate([0,0,0]) sled();
caps();
balls_preview();
