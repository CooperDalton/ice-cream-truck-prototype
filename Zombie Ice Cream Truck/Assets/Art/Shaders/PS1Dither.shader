// Full-screen PS1 look for the low-resolution game render shown on a RawImage: 4x4 ordered dither and per-channel
// color quantization. Pixelation itself comes from the small point-filtered render texture.
Shader "ZombieTruck/PS1 Dither"
{
    Properties
    {
        [PerRendererData] _MainTex ("Texture", 2D) = "white" {}
        _Levels ("Color Levels", Float) = 24
        _DitherStrength ("Dither Strength", Float) = 1
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" "PreviewType" = "Plane" }
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float _Levels;
            float _DitherStrength;

            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                o.color = v.color;
                return o;
            }

            static const float bayer[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };

            fixed4 frag(v2f i) : SV_Target
            {
                float2 texel = floor(i.uv * _MainTex_TexelSize.zw);
                float3 color = tex2D(_MainTex, (texel + 0.5) * _MainTex_TexelSize.xy).rgb;
                int index = (int)fmod(texel.x, 4) + (int)fmod(texel.y, 4) * 4;
                float threshold = (bayer[index] / 16.0 - 0.5) * _DitherStrength;
                color = floor(color * _Levels + threshold + 0.5) / _Levels;
                return fixed4(saturate(color), 1) * i.color;
            }
            ENDCG
        }
    }
}
