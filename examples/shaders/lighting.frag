#version 450

layout(location = 0) in vec3 frag_position;
layout(location = 1) in vec3 frag_normal;
layout(location = 2) in vec3 frag_color;

layout(location = 0) out vec4 out_color;

layout(set = 0, binding = 0) uniform Scene {
    mat4 view;
    mat4 projection;
    vec4 camera_pos;
    vec4 light_pos[4];
    vec4 light_color[4];
} scene;

void main()
{
    vec3 N = normalize(frag_normal);
    vec3 V = normalize(scene.camera_pos.xyz - frag_position);

    // Small ambient term prevents completely black back faces.
    vec3 result = frag_color * 0.035;

    for (int i = 0; i < 4; ++i)
    {
        vec3 to_light = scene.light_pos[i].xyz - frag_position;
        float distance_to_light = length(to_light);
        vec3 L = to_light / max(distance_to_light, 0.0001);

        // Smooth quadratic-ish attenuation. The light's .w is intensity.
        float attenuation =
            scene.light_color[i].w /
            (1.0 + 0.12 * distance_to_light +
             0.035 * distance_to_light * distance_to_light);

        // Lambert diffuse.
        float diffuse = max(dot(N, L), 0.0);

        // Blinn-Phong specular.
        vec3 H = normalize(L + V);
        float specular = pow(max(dot(N, H), 0.0), 64.0);

        vec3 light_rgb = scene.light_color[i].rgb;

        result += frag_color * light_rgb * diffuse * attenuation;
        result += light_rgb * specular * 0.45 * attenuation;
    }

    // Simple filmic-ish compression to keep the lights from blowing out.
    result = result / (result + vec3(1.0));

    // The swapchain is sRGB when supported, so leave this in linear space.
    out_color = vec4(result, 1.0);
}
