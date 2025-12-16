// DYNAMIXEL XL330 to 32P Gear Adapter
// Connects XL330-M288-T output shaft to 32-pitch 11-tooth gear with 5mm bore
// Design: Press-fit socket with set screw retention

// ===== PARAMETERS =====

// Gear specifications
gear_bore_diameter = 5.0;        // 5mm bore in your gear
gear_hub_height = 8.0;           // Height of shaft that goes into gear
set_screw_flat_depth = 0.5;      // Depth of flat for set screw

// DYNAMIXEL XL330 output shaft (measured from drawing)
// The output shaft appears to be approximately 6mm diameter with splines
shaft_diameter = 6.0;            // Approximate outer diameter of splined shaft
shaft_socket_depth = 6.0;        // How deep the socket goes onto shaft
shaft_socket_tolerance = 0.2;    // Clearance for press fit (adjust after test print)

// Adapter body
flange_diameter = 16.0;          // Diameter of mounting flange
flange_thickness = 3.0;          // Thickness of flange
total_height = flange_thickness + gear_hub_height;

// Set screw hole in gear (standard M3)
set_screw_diameter = 3.2;        // M3 clearance hole

// Spline approximation (8 splines typical for small DYNAMIXEL)
num_splines = 8;
spline_depth = 0.4;              // How deep splines cut into socket

// Print tolerance
hub_tolerance = -0.1;            // Negative = slightly smaller for tight fit

// ===== MODULES =====

module gear_hub() {
    difference() {
        // Main hub cylinder
        cylinder(h=gear_hub_height, d=gear_bore_diameter + hub_tolerance, $fn=50);
        
        // Flat for set screw
        translate([gear_bore_diameter/2 - set_screw_flat_depth, -gear_bore_diameter/2, 0])
            cube([set_screw_flat_depth + 1, gear_bore_diameter, gear_hub_height]);
    }
}

module splined_socket() {
    difference() {
        // Outer cylinder
        cylinder(h=shaft_socket_depth, d=shaft_diameter + 2, $fn=50);
        
        // Inner splined hole
        translate([0, 0, -0.1]) {
            // Base cylinder
            cylinder(h=shaft_socket_depth + 0.2, 
                    d=shaft_diameter + shaft_socket_tolerance, $fn=50);
            
            // Splines (radial cuts)
            for (i = [0:num_splines-1]) {
                rotate([0, 0, i * 360/num_splines])
                    translate([shaft_diameter/2 - spline_depth, -0.5, 0])
                        cube([spline_depth + 1, 1, shaft_socket_depth + 0.2]);
            }
        }
    }
}

module mounting_flange() {
    difference() {
        cylinder(h=flange_thickness, d=flange_diameter, $fn=50);
        
        // Optional: Add mounting holes for bolting to motor face
        // Uncomment if you want to bolt the adapter to the motor
        /*
        for (i = [0:3]) {
            rotate([0, 0, i * 90 + 45])
                translate([flange_diameter/2 - 2, 0, -0.1])
                    cylinder(h=flange_thickness + 0.2, d=2.5, $fn=20);
        }
        */
    }
}

// ===== MAIN ASSEMBLY =====

module adapter() {
    union() {
        // Bottom: Splined socket that mates with motor shaft
        translate([0, 0, 0])
            splined_socket();
        
        // Middle: Mounting flange
        translate([0, 0, shaft_socket_depth])
            mounting_flange();
        
        // Top: Gear hub that fits into 5mm bore
        translate([0, 0, shaft_socket_depth + flange_thickness])
            gear_hub();
    }
}

// ===== RENDER =====

adapter();

// ===== PRINT INSTRUCTIONS =====
// Material: PETG or Nylon (for strength and wear resistance)
// Layer height: 0.15mm or finer
// Infill: 100%
// Supports: None needed
// Orientation: Print with gear hub pointing UP (socket on build plate)
// 
// POST-PROCESSING:
// 1. Test fit on XL330 shaft - should be snug
// 2. If too tight, increase shaft_socket_tolerance
// 3. If too loose, decrease shaft_socket_tolerance
// 4. Sand the gear hub lightly if needed for smooth fit
//
// ASSEMBLY:
// 1. Press adapter onto XL330 output shaft (may need gentle tapping)
// 2. Slide gear onto hub
// 3. Align set screw with flat
// 4. Tighten set screw (don't overtighten - plastic will deform)
