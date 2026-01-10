board_w = 35;
board_l = 65;
board_h = 2;
hole_offset = 3;
hole_d = 3;

screen_w = 23;
screen_l = 35;
screen_h = 1;
screen_offset_l = 5;
screen_offset_w = 6;

knob_d = 14.5;
knob_h = 22;
knob_offset_l = 52.5 - board_l/2+1;
knob_offset_w = 0;

module screen(){
  color("black")
    translate([-board_w/2+screen_offset_l,
	       -board_l/2+screen_offset_w, 0])
    cube([screen_w, screen_l, screen_h]);
}

module screen_hole(){
    translate([-board_w/2+screen_offset_l-1,
	       -board_l/2+screen_offset_w-1, -5])
    cube([screen_w+2, screen_l+2, screen_h+10]);
}
inch = 25.4;
module pins(){
  translate([-board_w/2+.1*inch, -board_l/2 + .474*inch, -6]){
    for(i=[0:8]){
      translate([0, i * .1 * inch, 2])cube([1, 1, 10],center=true);
    }
    //translate([0,-9,0])cylinder(d=3.5, h=10, $fn=30);
  }
}
module knob(){
  translate([knob_offset_w, knob_offset_l, 0])color("darkgrey")cylinder(d=knob_d, h=knob_h);
}

module knob_hole(){
  translate([knob_offset_w, knob_offset_l, -5])rotate([0,0,45])
    cylinder(d=knob_d+4, h=knob_h+10, $fn=40);
}

module display_board(){
  difference(){
    color("darkblue")translate([0,0,-board_h/2])cube([board_w, board_l, board_h], center=true);
    for(i=[-1,1]){
      for(j=[-1,1]){
	translate([i * (board_w/2 - hole_offset), j * (board_l/2 - hole_offset), 0])
	  cylinder(d=hole_d, h=10, center=true, $fn=30);
      }
    }
  }
}

module button(){
  translate([0,0,1])cube([2, 4, 2], center=true);
}
module buttons(){
  translate([knob_offset_w-12, knob_offset_l, 0])color("lightgrey")button();
  translate([knob_offset_w+12, knob_offset_l, 0])color("lightgrey")button();
}

module display_assy(){
  translate([0,0,-2.5]){
    display_board();
    screen();
    knob();
    pins();
    buttons();
  }
}

module display_screws(){
  for(i=[-1,1]){
    for(j=[-1,1]){
      translate([i * (board_w/2 - hole_offset), j * (board_l/2 - hole_offset), 0])
	cylinder(d=hole_d+.5, h=30, center=true, $fn=30);
    }
  }
}

module display_spacer(){
  $fn=30;
  difference(){
    cylinder(d=8, h=2.5);
    translate([0,0,-1])cylinder(d=3.5, h=2.5+2);
  }
}
module display_spacers(){
  translate([0,0,-2.5])
  for(i=[-1,1]){
    for(j=[-1,1]){
      translate([i * (board_w/2 - hole_offset), j * (board_l/2 - hole_offset), 0])display_spacer();
    }
  }
}
//display_spacers();
//buttons();
display_assy();
//translate([0,0,0])screen_hole();
