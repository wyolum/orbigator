// Render all components in their assembly positions
// Usage: Set RENDER_PART to the component you want to export, then:
//   openscad -o stls_in_situ/<part>.stl -D 'RENDER_PART="<part>"' render_in_situ.scad
//
// Example:
//   openscad -o stls_in_situ/aov_motor_mount.stl -D 'RENDER_PART="aov_motor_mount"' render_in_situ.scad

// Which part to render (set via command line -D option)
RENDER_PART = "aov_arm";  // default

// Include dependencies
include <aov_arm.scad>
use <flange.scad>
use <sled.scad>

// Constants from full_assembly.scad
inch = 25.4;
globe_d = 13 * inch;
globe_r = globe_d / 2;

// Assembly parameters (from line 382: aov_motor_assy(65, 90))
inc = 65;
aov = 90;

// Module to import STL files
module import_stl(name) {
    import(str("stls/", name, ".stl"));
}

// ============================================
// Component transformations from full_assembly.scad
// ============================================

// aov_arm: from aov_motor_assy
module render_aov_arm() {
    translate([0, 0, -140])
        translate([0, -3, 140])
            rotate([inc, 0, 0])
                rotate([0, 0, aov-180])
                    aov_arm();
}

// aov_motor_mount: from aov_motor_assy
module render_aov_motor_mount() {
    translate([0, 0, -140])
        translate([0, 0, 150])
            translate([0, 0, -10])
                rotate([inc, 0, 0])
                    rotate([0, 180, 0])
                        aov_motor_mount();
}

// sled: from aov_motor_assy
module render_sled() {
    translate([0, 0, -140])
        translate([0, -3, 140])
            rotate([inc, 0, 0])
                rotate([0, 0, aov-180])
                    translate([-globe_r, 0, 0])
                        sled();
}

// ring_gear: from Ring module
module render_ring_gear() {
    translate([0, 0, -150])
        import_stl("ring_gear");
}

// drive_gear: from eqx_motor_assy (commented out in main assembly)
module render_drive_gear() {
    // r = R - n * pitch / PI / 2 where R = N * pitch / PI / 2
    // With N=120, n=14, pitch=2.494: R≈47.6, r≈36.5
    pitch = 2.494;
    N = 120;
    n = 14;
    R = N * pitch / PI / 2;
    r = R - n * pitch / PI / 2;
    translate([0, 0, -150])
        translate([0, r, 0])
            import_stl("drive_gear");
}

// base_with_1010_hole: at origin (commented out in main assembly)
module render_base_with_1010_hole() {
    import_stl("base_with_1010_hole");
}

// RingLock: from RingLock module
module render_RingLock() {
    pitch = 2.494;
    N = 120;
    n = 14;
    R = N * pitch / PI / 2;
    r = R - n * pitch / PI / 2;
    translate([0, -r, -146])
        import_stl("RingLock");
}

// idler: from idlers module (multiple instances)
module render_idler() {
    pitch = 2.494;
    N = 120;
    n = 14;
    R = N * pitch / PI / 2;
    r = R - n * pitch / PI / 2;
    // First idler position (i=1)
    translate([0, 0, -151])
        translate([r * sin(60), r * cos(60), 0])
            import_stl("idler");
}

// spring_arms: from spring module
module render_spring_arms() {
    translate([0, 0, -150])
        rotate([0, 0, 90])
            import_stl("spring_arms");
}

// pico: from aov_motor_assy
module render_pico() {
    translate([0, 0, -140])
        translate([0, 0, 150])
            translate([0, 0, -10])
                rotate([inc, 0, 0])
                    rotate([0, 180, 0])
                        translate([0, 10, 40])
                            rotate([90, 0, 180])
                                import_stl("pi-pico-2w-cad-reference");
}

// ============================================
// Render selected part
// ============================================

if (RENDER_PART == "aov_arm") render_aov_arm();
else if (RENDER_PART == "aov_motor_mount") render_aov_motor_mount();
else if (RENDER_PART == "sled") render_sled();
else if (RENDER_PART == "ring_gear") render_ring_gear();
else if (RENDER_PART == "drive_gear") render_drive_gear();
else if (RENDER_PART == "base_with_1010_hole") render_base_with_1010_hole();
else if (RENDER_PART == "RingLock") render_RingLock();
else if (RENDER_PART == "idler") render_idler();
else if (RENDER_PART == "spring_arms") render_spring_arms();
else if (RENDER_PART == "pico") render_pico();
else echo(str("Unknown part: ", RENDER_PART));
