// 2D projection wrapper for full_assembly.scad
// This projects the 3D assembly onto the XY plane for SVG export

// Temporarily remove problematic includes
//include <arduino.scad>
include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>
use <dynamixel_motor.scad>
use <inclination_aov_mount.scad>
use <flange.scad>
use <sled.scad>
use <spring.scad>
use <spring_ring.scad>
use <dynamixel_aov_arm.scad>
use <main_board.scad>
use <display_encoder_board.scad>

projection(cut = false) {
    // Import the main modules from full_assembly
    // You can selectively choose which parts to project
    
    // Copy key parameters from full_assembly.scad
    inch = 25.4;
    N = 60 * 2;
    n = 7 * 2;
    pitch = 2.494;
    h = 8;
    globe_d = 299;
    globe_r = globe_d/2;
    base_z_offset = 150 - (globe_d - 13 * inch)/2;
    R = N * pitch / PI / 2;
    r = R - n * pitch / PI / 2;
    
    // Include and render the Ring (currently the active module in full_assembly.scad)
    // You can modify this to render other parts
    use <full_assembly.scad>
    translate([0,0,17]) Ring();
}
