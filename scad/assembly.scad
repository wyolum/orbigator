/*
 * Full Assembly for Orbigator
 * Refactored into logical components
 */

include <common.scad>
include <motor_dynamixel.scad>
include <mount_aov.scad>
include <arm_aov.scad>
include <gears.scad>
include <base.scad>
include <display.scad>
include <electronics.scad>
include <sled.scad>
include <misc.scad>
include <globe.scad>

// Assembly modules
module eqx_motor_assy(){
  translate([0,0,-base_z_offset+16.5]){
    translate([0, r, 17.8 + motor_height - h/2])rotate([0,180,0])dynamixel_xl330();
    translate([0, r, 17.8 - h/2])rotate([0,180,0])dynamixel_drive_shaft();
    translate([0, r, -2.8])drive_gear();
  }
}

module aov_motor_assy(inc, aov){
  translate([0, 0, 0])
    rotate([inc, 0, 0])rotate([0, 180, 0]){
    rotate([0,180,90])translate([0,0,-horn_height])dynamixel_xl330();
    color("coral")dynamixel_motor_mount();
  }
  translate([0, 0, 0])
    rotate([inc, 0, 0])rotate([0, 0, aov-180]){
    color([.4, .4, .4, 1])aov_arm();
    translate([-globe_r, 0, 0])rotate([0, -90, 0])sled();
    translate([-globe_r, 0, 0])rotate([0, -90, 0])magnets();
  }
}

module base_with_extension(){
  base_with_1010_hole();
  translate([0,0,-inch])display_extension();
}

// Rendering
translate([0,0,inch/2]){
  base_with_extension();
  translate([0,0,16.4])color("cornflowerblue")Ring();
  eqx_motor_assy();
  aov_motor_assy(65, 120);
  
  // Optional components
  // globe();
}

// Test shared constants
echo("Motor Horn Diameter:", horn_diameter);
echo("Motor Horn Height:", horn_height);
