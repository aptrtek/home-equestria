shader_type spatial;
// Vertical gores, matching the visible Mare Fair balloon
// (https://2025.marefair.org/_astro/mf_desktop.iPluWSMU_EDpGb.png).
// Stripes follow the angle around the model, so they need no particular UVs.

uniform vec4 red_color : source_color = vec4(0.941176, 0.282353, 0.313725, 1.0);
uniform vec4 blue_color : source_color = vec4(0.490196, 0.705882, 0.878431, 1.0);
uniform float stripe_count = 8.0;
uniform float roughness_amount : hint_range(0.0, 1.0) = 0.78;

varying vec3 local_position;

void vertex() {
	local_position = VERTEX;
}

void fragment() {
	float turn = atan(local_position.z, local_position.x) / TAU + 0.5;
	ALBEDO = fract(turn * stripe_count) < 0.5 ? red_color.rgb : blue_color.rgb;
	ROUGHNESS = roughness_amount;
}
