/*
 * Orbigator Base Assembly
 * Integrates EQX motor, gear train, controller, display, and encoder
 * 
 * WARNING: AI-generated attempt - probably needs significant refinement!
 * Author: Antigravity (with low confidence in 3D design)
 * Date: 2025-12-20
 */

use <dynamixel_motor.scad>

// Import motor constants
// motor_width = 20
// motor_depth = 34
// motor_height = 23
// bracket_hole_spacing_x = 16
// bracket_hole_spacing_y = 30

// Unit conversions
inch = 25.4;

// Globe parameters (from aov_arm)
globe_d = 13 * inch;
globe_r = globe_d/2;

// Base platform parameters
base_diameter = 200;  // Large enough for all components
base_thickness = 5;
base_height = 10;  // Height for mounting posts

// EQX motor gear parameters
drive_gear_teeth = 11;
ring_gear_teeth = 120;
gear_module = 1.5;  // Metric module
ring_gear_diameter = ring_gear_teeth * gear_module;

// Pico 2 board dimensions (approximate)
pico_length = 51;
pico_width = 21;
pico_thickness = 1;
pico_mount_hole_spacing_x = 47;
pico_mount_hole_spacing_y = 11.4;
pico_standoff_height = 8;

// OLED display dimensions (128x64 typical module)
oled_width = 27;
oled_length = 27;
oled_thickness = 4;
oled_screen_width = 23;
oled_screen_length = 12;

// Rotary encoder dimensions
encoder_diameter = 12;
encoder_shaft_length = 15;
encoder_mount_diameter = 7;  // Panel mount hole

// Component positioning
eqx_motor_x = 0;
eqx_motor_y = 0;
pico_x = 60;
pico_y = 0;
oled_x = -60;
oled_y = 40;
encoder_x = -60;
encoder_y = -40;

// Mounting screw parameters
m2_hole = 2.2;
m3_hole = 3.2;
m3_nut_width = 5.5;
m3_nut_height = 2.4;

$fn = 50;

// Main base platform
module base_platform() {
    difference() {
        union() {
            // Main circular base
            cylinder(d=base_diameter, h=base_thickness);
            
            // Reinforcement ribs
            for (angle = [0:45:315]) {
                rotate([0, 0, angle])
                    translate([0, -2, base_thickness/2])
                        cube([base_diameter/2 - 20, 4, base_thickness], center=true);
            }
        }
        
        // Central hole for globe shaft/mechanism
        cylinder(d=40, h=base_thickness + 2, center=true);
        
        // Weight reduction holes (optional)
        for (angle = [0:60:300]) {
            rotate([0, 0, angle])
                translate([base_diameter/3, 0, -1])
                    cylinder(d=15, h=base_thickness + 2);
        }
    }
}

// EQX motor mount
module eqx_motor_mount() {
    translate([eqx_motor_x, eqx_motor_y, base_thickness]) {
        difference() {
            // Mounting bracket
            translate([0, 0, 2.5])
                cube([30, 40, 5], center=true);
            
            // Motor mounting holes (from dynamixel_motor.scad)
            for (x = [-1, 1]) {
                for (y = [-1, 1]) {
                    translate([x * 16/2, y * 30/2, 0])
                        cylinder(d=m2_hole, h=20, center=true);
                }
            }
        }
    }
}

// Pico 2 mounting posts
module pico_mount() {
    translate([pico_x, pico_y, base_thickness]) {
        for (x = [-1, 1]) {
            for (y = [-1, 1]) {
                translate([x * pico_mount_hole_spacing_x/2, 
                          y * pico_mount_hole_spacing_y/2, 
                          0]) {
                    difference() {
                        // Standoff post
                        cylinder(d=6, h=pico_standoff_height);
                        // M2 screw hole
                        translate([0, 0, -1])
                            cylinder(d=m2_hole, h=pico_standoff_height + 2);
                    }
                }
            }
        }
        
        // Support base
        translate([0, 0, pico_standoff_height/2])
            cube([pico_length + 4, pico_width + 4, pico_standoff_height], center=true);
    }
}

// OLED display mount
module oled_mount() {
    translate([oled_x, oled_y, base_thickness]) {
        difference() {
            union() {
                // Angled mounting bracket
                rotate([60, 0, 0])
                    translate([0, 0, 10])
                        cube([oled_width + 8, oled_length + 8, 3], center=true);
                
                // Support strut
                translate([0, -5, 5])
                    cube([oled_width + 8, 10, 10], center=true);
            }
            
            // Screen viewing window
            rotate([60, 0, 0])
                translate([0, 0, 10])
                    cube([oled_screen_width, oled_screen_length, 10], center=true);
            
            // Mounting holes (typical OLED module has 4 corner holes)
            rotate([60, 0, 0]) {
                for (x = [-1, 1]) {
                    for (y = [-1, 1]) {
                        translate([x * (oled_width - 4)/2, 
                                  y * (oled_length - 4)/2, 
                                  8])
                            cylinder(d=m2_hole, h=10);
                    }
                }
            }
        }
    }
}

// Rotary encoder mount
module encoder_mount() {
    translate([encoder_x, encoder_y, base_thickness]) {
        difference() {
            union() {
                // Mounting boss
                cylinder(d=20, h=15);
                
                // Reinforcement to base
                translate([0, 0, 7.5])
                    cube([20, 20, 15], center=true);
            }
            
            // Encoder shaft hole
            translate([0, 0, -1])
                cylinder(d=encoder_mount_diameter, h=20);
            
            // Nut trap for encoder mounting nut
            translate([0, 0, 12])
                cylinder(d=12, h=5, $fn=6);
        }
    }
}

// Ring gear mount (for EQX gearing)
module ring_gear_mount() {
    translate([0, 0, base_thickness + 10]) {
        difference() {
            // Mounting ring
            cylinder(d=ring_gear_diameter + 20, h=5);
            
            // Center clearance for globe shaft
            cylinder(d=ring_gear_diameter - 10, h=10, center=true);
            
            // Gear teeth clearance (simplified)
            cylinder(d=ring_gear_diameter + 2, h=10, center=true);
        }
    }
}

// Cable management clips
module cable_clip(position) {
    translate(position) {
        difference() {
            cube([8, 12, 6], center=true);
            
            // Cable channel
            translate([0, 0, 2])
                rotate([0, 90, 0])
                    cylinder(d=6, h=10, center=true);
        }
    }
}

// Assembly
module orbigator_base_assembly() {
    color("lightblue") {
        base_platform();
        eqx_motor_mount();
        pico_mount();
        oled_mount();
        encoder_mount();
        
        // Cable management clips
        cable_clip([70, 30, base_thickness + 3]);
        cable_clip([70, -30, base_thickness + 3]);
        cable_clip([-70, 0, base_thickness + 3]);
    }
}

// Render
orbigator_base_assembly();

// Optional: Show component placeholders for visualization
if (false) {
    // EQX motor
    translate([eqx_motor_x, eqx_motor_y, base_thickness + 5])
        color("darkgray", 0.5)
            cube([20, 34, 23], center=true);
    
    // Pico board
    translate([pico_x, pico_y, base_thickness + pico_standoff_height])
        color("green", 0.5)
            cube([pico_length, pico_width, pico_thickness], center=true);
    
    // OLED display
    translate([oled_x, oled_y, base_thickness + 15])
        rotate([60, 0, 0])
            color("blue", 0.5)
                cube([oled_width, oled_length, oled_thickness], center=true);
    
    // Encoder
    translate([encoder_x, encoder_y, base_thickness + 10])
        color("silver", 0.5)
            cylinder(d=encoder_diameter, h=encoder_shaft_length);
}
