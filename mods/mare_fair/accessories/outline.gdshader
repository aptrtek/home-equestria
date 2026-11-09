shader_type spatial;
// A thin dark outline for the removable hat and glasses, to match the hair's drawn line.
render_mode unshaded, cull_front;

uniform vec4 line_color : source_color = vec4(0.13, 0.11, 0.12, 1.0);
uniform float width = 0.0028;

void vertex() {
	VERTEX += NORMAL * width;
}

void fragment() {
	ALBEDO = line_color.rgb;
}
