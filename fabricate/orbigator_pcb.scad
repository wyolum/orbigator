use <display_encoder_board.scad>

module orbigator_board(){
  color("darkgray")difference(){
    translate([-5, 0, 0])cube([50.5, 70, 1.6], center=true);
    display_screws();
  }
}
