// Simplified ISS 2D Extrusion Model
// Designed for small scale 3D printing (1.5 inch wingspan)
// Enforces minimum feature width of 0.4mm

$fn = 64;

// --- Parameters ---
TARGET_WIDTH_MM = 38.1; // 1.5 inches
EXTRUSION_HEIGHT_MM = 1; 
MIN_FEATURE_MM = 0.4;

// --- Real World Proportions (Adjusted for 4:3 Aesthetic) ---
REAL_TRUSS_WIDTH_M = 109.0;
REAL_TRUSS_THICKNESS_M = 5.0; 

// Target Aspect Ratio: 4:3 (Width:Height)
// If Width is 109m equivalent, Height should be 109 * (3/4) = 81.75m equivalent.
// We will stretch the Solar Arrays and Spine to fill this "Virtual Box".

// Solar Array Total Span -> 81.75m
// Single Panel Length = 81.75m / 2 = ~41m (vs 34m real)
REAL_PANEL_LENGTH_M = 41.0;   
REAL_PANEL_WIDTH_M = 12.0;    

// Module Spine Total Length -> ~60m (USOS + ROS)
REAL_MODULE_LENGTH_M = 60.0;
REAL_MODULE_DIA_M = 4.5;

// --- Scaling ---
SCALE = TARGET_WIDTH_MM / REAL_TRUSS_WIDTH_M;

// Helper: robust dimension
function dim(d) = max(d * SCALE, MIN_FEATURE_MM);


module iss_2d() {
    
    // 1. Integrated Truss Structure (Main Horizontal Beam)
    truss_w = TARGET_WIDTH_MM;
    truss_h = dim(2.5); // Thicker main truss
    
    color("silver")
    translate([-truss_w/2, -truss_h/2, 0])
        square([truss_w, truss_h]);

    // 2. Pressurized Modules (Vertical Spine - Asymmetric)
    // USOS (Prograde/Forward) - "Top" in this view
    // ROS (Retrograde/Aft) - "Bottom" in this view
    
    // Core Module Widths
    mod_clipper_w = dim(4.2); // USOS is wider
    mod_ros_w = dim(3.0);     // Zarya/Zvezda narrower
    
    // USOS Stack (Nodes, Lab, JEM, Columbus) -> Extends 'Up' (Y+)
    usos_len = dim(15.0);
    translate([-mod_clipper_w/2, 0, 0])
        square([mod_clipper_w, usos_len]);
        
    // ROS Stack (Zarya, Zvezda) -> Extends 'Down' (Y-)
    // Zarya (FGB)
    zarya_len = dim(12.0);
    translate([-mod_ros_w/2, -zarya_len, 0])
        square([mod_ros_w, zarya_len]);
        
    // Zvezda (SM) - Further down, slightly narrower/different
    zvezda_len = dim(12.0);
    zvezda_w = dim(2.8);
    translate([-zvezda_w/2, -zarya_len - zvezda_len, 0])
        square([zvezda_w, zvezda_len]);
        
    // Kibo Porch (JEM-EF) - Sticking out Left on USOS
    jem_w = dim(8.0);
    jem_h = dim(3.0);
    translate([-jem_w, 5.0*SCALE, 0]) // Offset up slightly
        square([jem_w, jem_h]);


    // 3. Solar Arrays (The "H" Shape - 4 Main Pairs)
    // S6, S4, P4, P6 (Ends of Truss)
    panel_l = dim(REAL_PANEL_LENGTH_M);
    panel_w = dim(REAL_PANEL_WIDTH_M);
    
    pos_outer = (TARGET_WIDTH_MM / 2) - (panel_w / 2);
    pos_inner = pos_outer - panel_w - dim(5.0); 

    module solar_pair() {
        translate([-panel_w/2, -panel_l/2, 0])
            square([panel_w, panel_l]);
    }

    color("orange") {
        translate([pos_outer, 0, 0]) solar_pair(); // S6
        translate([pos_inner, 0, 0]) solar_pair(); // S4
        translate([-pos_outer, 0, 0]) solar_pair(); // P6
        translate([-pos_inner, 0, 0]) solar_pair(); // P4
    }
    
    // 4. "8 Interior Panels" (User Request)
    // Interpreted as: 
    // - 6 Vertical Radiators (3 Port, 3 Starboard on Truss)
    // - 2 Horizontal Panels (ROS / Zvezda Wings)
    
    // A. 6 Vertical Radiators (HRSR)
    // Located on S1 and P1 trusses (inboard of main arrays)
    rad_w = dim(2.5);
    rad_l = dim(10.0); // Extend 'down' (trailing) usually
    rad_pitch = dim(3.5); // Spacing
    
    rad_start_x = dim(8.0); // Distance from center
    
    color("white") {
        // Starboard Radiators (3)
        for(i=[0:2]) {
             translate([rad_start_x + (i*rad_pitch), -rad_l, 0])
                square([rad_w, rad_l]);
        }
        
        // Port Radiators (3)
        for(i=[0:2]) {
             translate([-rad_start_x - (i*rad_pitch) - rad_w, -rad_l, 0])
                square([rad_w, rad_l]);
        }
    }
    
    // B. 2 Horizontal Panels (ROS Solar Arrays)
    // Attached to Zvezda (Aft module)
    ros_panel_span = dim(25.0); // Total span
    ros_panel_h = dim(3.0);     // Thickness (N/S in this view? No, Horiz means E/W)
    // If "2 Horiz" means parallel to Truss (Left/Right)
    
    translate([-ros_panel_span/2, -zarya_len - (zvezda_len/2) - (ros_panel_h/2), 0])
        square([ros_panel_span, ros_panel_h]);
}

// Extrude the 2D shape
difference(){
  union(){
    linear_extrude(height = EXTRUSION_HEIGHT_MM)
      iss_2d();
    cylinder(d=4, h=EXTRUSION_HEIGHT_MM);
  }
  translate([0,0,-1])cylinder(d=2, h=EXTRUSION_HEIGHT_MM+2);
}
