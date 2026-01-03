/*
 * Common Constants and Units
 */

inch = 25.4;
$fn = 50;
$show_demo = false;

// Globe parameters
globe_d = 299; 
globe_r = globe_d/2;

// Base and Gear parameters
pitch = 2.494; // was 2.5
h = 8;         // Gear thickness
N = 60 * 2;    // Number of teeth for ring gear
n = 7 * 2;     // Number of teeth for drive gear

// Calculated radii
R = N * pitch / PI / 2; // Ring gear radius
r = R - n * pitch / PI / 2; // Drive gear center radius

// Z-offset for base relative to globe center
base_z_offset = 150 - (globe_d - 13 * inch)/2;
