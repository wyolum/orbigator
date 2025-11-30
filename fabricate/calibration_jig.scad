include <aov_arm.scad>

// Calibration Jig for Orbigator Z-Axis
// This part mounts in place of the main arm.
// It features "feelers" that should barely touch the globe's inner surface
// if the mechanism is perfectly centered.

module calibration_jig(){
    // Import base dimensions from aov_arm.scad
    // globe_ir is the target radius
    
    feeler_len = 10;
    feeler_w = 4;
    
    difference(){
        union(){
            // 1. Mounting Base (same as arm)
            cylinder(d=flange_d + 4, h=height);
            
            // 2. Main Arc (Rigid spine)
            intersection(){
                difference(){
                    cylinder(r=globe_ir - 2, h=height);
                    cylinder(r=globe_ir - 12, h=height);
                }
                // Quarter circle sector
                cube([globe_ir, globe_ir, height]);
            }
            
            // 3. Feelers (Touch points)
            // Point A: Near Equator (0 deg)
            translate([globe_ir - 2, 0, height/2])
                cube([4, feeler_w, feeler_w], center=true);
                
            // Point B: 45 degrees
            rotate([0,0,45])
                translate([globe_ir - 2, 0, height/2])
                cube([4, feeler_w, feeler_w], center=true);
                
            // Point C: Near Pole (80 deg)
            rotate([0,0,80])
                translate([globe_ir - 2, 0, height/2])
                cube([4, feeler_w, feeler_w], center=true);
        }
        
        // Mounting Holes (copied from aov_arm)
        translate([0,0,-1])cylinder(h=height*2, d=10); // Center clearance
        for(i=[1:4]){
            rotate([0,0,45 + 90 * i])
            translate([8,0,-1])
            cylinder(d=3.5, h=30, $fn=30);
        }
    }
    
    // Instructions text engraved
    color("red")
    translate([15, 5, height])
    linear_extrude(1)
    text("CALIBRATION", size=4);
}

calibration_jig();
