use <display_encoder_board.scad>


main_w = 55;
main_l = 70;
main_h = 3;

module ds3231(){
  color("black")cube([10, 12, 1.5], center=true);
}

inch = 25.4;
module motor_jack(){
  color("blue")cube([.2 * inch, 10.5, 8],center=true);
}

module chip_74hc126(){
    color("darkgrey")cube([.8*inch, .3*inch, 4],center=true);
}

module barrel_jack(){
  translate([0,0,-2])difference(){
    color([.2, .2, .2])cube([11, 5, 7.5], center=true);
    translate([1, 0, 0])rotate([0, 90, 0])cylinder(d=4.2, h=10, $fn=20);
  }
}

module mounting_screws(){
  display_screws();
}

module main_board(){
  difference(){
    color("darkgreen")cube([main_w, main_l, main_h], center=true);
    display_screws();
  }
}

module main_assy(){
  translate([0,0,-5-2.3]){
    translate([-7,-5,-5])motor_jack();
    translate([-5,-20,-2])ds3231();
    translate([15,-20,-3])chip_74hc126();
    translate([25,0,-3])barrel_jack();
    
    translate([0,0,5])display_assy();
    translate([0, 15, -3])rotate([0,180,90])color("grey")import("stls/pi-pico-2w-cad-reference.stl");
    main_board();
  }
}

main_assy();

