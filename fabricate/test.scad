// OrbiGator base – rev2 (print-friendly)
// No libs required; fillets are simple bevels.
//
// ---------- Params ----------
$fn = 128;

// Base disk under dome
base_d          = 78;     // guess from pics; set to your real value
base_t          = 4;      // thickness

// Dome (frustum)
dome_d_base     = 60;     // from your note
dome_d_top      = 35;
dome_h          = 33;

// Feet (3x)
foot_rad        = 42.18;  // center radius
foot_h          = 10;
foot_d_top      = 14;     // wider at top for conical boss
foot_d_bot      = 18;     // flared base
foot_hole_d     = 4.5;    // through-hole

// Web ribs
web_t_at_foot   = 8;      // thickness at foot
web_t_at_dome   = 4;      // thickness at dome
web_h           = 15;     // height
web_w           = 20;     // width of each web “wedge” at the foot

// Top plate
plate_t         = 10;
plate_len       = 59.18;
plate_w         = 23;
plate_z         = dome_h - plate_t + 0.001; // sit on dome
plate_x_left    = -plate_len/2;             // center-ish

// Plate holes
bore_d          = 25;
bore_x_from_left= 23;
bore_y_offset   = 0;
m3_d            = 3;
m3_pitch_x      = 20;     // TODO: your exact pattern
m3_pitch_y      = 16;     // TODO: your exact pattern

// Square cutouts
square_plate_d  = 10;     // in plate
square_plate_x  = 35;     // TODO: confirm exact inset
square_plate_y  = 0;
square_dome_d   = 10;     // 10×10 window through dome
square_dome_z   = 8;      // height where it pierces

// Small chamfers/fillets (simple)
edge_chamfer    = 0.8;    // bevel on foot top and plate top holes

// ---------- Helpers ----------
module chamfer_cyl(d,h,c=0.6){
    // quick-and-dirty top bevel
    difference(){
        cylinder(d=d,h=h);
        translate([0,0,h-c]) cylinder(d1=d-2*c, d2=d, h=c+0.01);
    }
}

module foot_cone(){
    // truncated cone + through hole + top chamfer
    difference(){
        // cone
        cylinder(h=foot_h, d1=foot_d_bot, d2=foot_d_top);
        // hole
        translate([0,0,-1]) cylinder(d=foot_hole_d, h=foot_h+2);
        // top bevel of hole
        translate([0,0,foot_h-edge_chamfer])
            cylinder(d1=foot_hole_d-2*edge_chamfer, d2=foot_hole_d, h=edge_chamfer+0.01);
    }
}

module dome(){
    // base disk + frustum
    union(){
        cylinder(d=base_d, h=base_t);                         // base disk
        translate([0,0,base_t]) cylinder(h=dome_h, d1=dome_d_base, d2=dome_d_top);  // dome
    }
}

module web_wedge(){
    // tapered web from foot toward dome (thicker at foot)
    hull(){
        translate([0,0,base_t])
            cube([web_w, web_t_at_foot, web_h], center=true);
        translate([- (foot_rad - dome_d_base/2) , 0, base_t])
            cube([web_w*0.4, web_t_at_dome, web_h*0.9], center=true);
    }
}

module top_plate(){
    translate([plate_x_left, -plate_w/2, plate_z + base_t])
    difference(){
        cube([plate_len, plate_w, plate_t]);
        // main bore
        translate([bore_x_from_left, plate_w/2 + bore_y_offset, -1])
            cylinder(d=bore_d, h=plate_t+2);
        // bore chamfer (top)
        translate([bore_x_from_left, plate_w/2 + bore_y_offset, plate_t-edge_chamfer])
            cylinder(d1=bore_d-2*edge_chamfer, d2=bore_d, h=edge_chamfer+0.02);

        // 4× M3 pattern
        for (sx=[-m3_pitch_x/2, m3_pitch_x/2])
        for (sy=[-m3_pitch_y/2, m3_pitch_y/2])
            translate([bore_x_from_left+sx, plate_w/2+bore_y_offset+sy, -1])
                cylinder(d=m3_d, h=plate_t+2);

        // square in plate
        translate([square_plate_x, plate_w/2 + square_plate_y, plate_t/2])
            cube([square_plate_d, square_plate_d, plate_t+2], center=true);
    }
}

// ---------- Assembly ----------
difference(){
    union(){
        // Dome + base disk
        dome();

        // Feet (3x)
        for (a=[0,120,240])
            rotate([0,0,a]) translate([foot_rad,0,0]) foot_cone();

        // Webs (aligned to each foot)
        for (a=[0,120,240])
            rotate([0,0,a]) translate([foot_rad - web_w/2,0,0]) web_wedge();

        // Plate
        top_plate();
    }

    // Square window through dome
    translate([0,0,base_t+square_dome_z])
        cube([square_dome_d, square_dome_d, dome_h+5], center=true);
}
