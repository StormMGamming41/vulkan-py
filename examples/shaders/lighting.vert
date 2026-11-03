#version 450

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec3 in_color;

layout(location = 0) out vec3 frag_position;
layout(location = 1) out vec3 frag_normal;
layout(location = 2) out vec3 frag_color;

layout(set = 0, binding = 0) uniform Scene {
    mat4 view;
    mat4 projection;
    vec4 camera_pos;
    vec4 light_pos[4];
    vec4 light_color[4];
} scene;

layout(push_constant) uniform PushConstants {
    mat4 model;
} push_constants;

void main()
{
    vec4 world_position = push_constants.model * vec4(in_position, 1.0);
    mat3 normal_matrix = transpose(inverse(mat3(push_constants.model)));

    frag_position = world_position.xyz;
    frag_normal = normalize(normal_matrix * in_normal);
    frag_color = in_color;

    gl_Position = scene.projection * scene.view * world_position;
}
