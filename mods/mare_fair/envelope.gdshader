shader_type spatial;
// Vertical gores, matching the visible Mare Fair balloon
// (https://2025.marefair.org/_astro/mf_desktop.iPluWSMU_EDpGb.png).
// UV.x runs around the envelope.

uniform vec4 red_color : source_color = vec4(0.941176, 0.282353, 0.313725, 1.0);
uniform vec4 blue_color : source_color = vec4(0.376471, 0.564706, 0.815686, 1.0);
uniform float stripe_count = 8.0;
uniform float roughness_amount : hint_range(0.0, 1.0) = 0.78;

void fragment() {
	float band = fract(UV.x * stripe_count);
	ALBEDO = band < 0.5 ? red_color.rgb : blue_color.rgb;
	ROUGHNESS = roughness_amount;
}
