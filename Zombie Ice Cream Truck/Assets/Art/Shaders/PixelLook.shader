// Distance-aware pixel look, run on the 1920 x 1080 game render by PixelLookFeature (a URP full-screen pass with the
// depth requirement on). Near surfaces get big pixels and far surfaces smaller ones, so distant zombies keep enough
// pixels to read. Then a 4x4 ordered dither and per-channel color quantization on each pixel's own grid.
Shader "ZombieTruck/Pixel Look"
{
    Properties
    {
        _Coarse ("Near Pixel Size", Float) = 4
        _Medium ("Mid Pixel Size", Float) = 2
        _Fine ("Far Pixel Size", Float) = 1
        _MediumFrom ("Mid Pixels From (m)", Float) = 18
        _FineFrom ("Far Pixels From (m)", Float) = 45
        _Levels ("Color Levels", Float) = 24
        _DitherStrength ("Dither Strength", Float) = 1
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        ZWrite Off ZTest Always Cull Off Blend Off
        Pass
        {
            Name "Pixel Look"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            float _Coarse;
            float _Medium;
            float _Fine;
            float _MediumFrom;
            float _FineFrom;
            float _Levels;
            float _DitherStrength;

            static const float bayer[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };

            // Distance from the camera in meters at a screen pixel position.
            float EyeDepth(float2 pixel)
            {
                return LinearEyeDepth(SampleSceneDepth(pixel * _BlitTexture_TexelSize.xy), _ZBufferParams);
            }

            half4 Frag(Varyings input) : SV_Target
            {
                // Each level decides from the depth at the middle of its own cell, so every screen pixel in a cell
                // makes the same choice and the cells tile without gaps.
                float2 pixel = input.texcoord * _BlitTexture_TexelSize.zw;
                float size = _Coarse;
                float2 center = (floor(pixel / size) + 0.5) * size;
                float depth = EyeDepth(center);
                if (depth > _MediumFrom)
                {
                    size = _Medium;
                    center = (floor(pixel / size) + 0.5) * size;
                    depth = EyeDepth(center);
                }
                if (depth > _FineFrom)
                {
                    size = _Fine;
                    center = (floor(pixel / size) + 0.5) * size;
                }
                float3 color = SAMPLE_TEXTURE2D_X_LOD(_BlitTexture, sampler_PointClamp, center * _BlitTexture_TexelSize.xy, 0).rgb;

                float2 cell = floor(pixel / size);
                int index = (int)fmod(cell.x, 4) + (int)fmod(cell.y, 4) * 4;
                float threshold = (bayer[index] / 16.0 - 0.5) * _DitherStrength;
                color = floor(color * _Levels + threshold + 0.5) / _Levels;
                return half4(saturate(color), 1);
            }
            ENDHLSL
        }
    }
}
