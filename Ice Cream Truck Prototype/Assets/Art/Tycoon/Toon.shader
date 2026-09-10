Shader "Ice Cream/Toon"
{
    Properties { _BaseColor("Color", Color) = (1,1,1,1) }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            CBUFFER_END
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct V { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float3 positionWS : TEXCOORD1; };
            V vert(A i) { V o; o.positionWS=TransformObjectToWorld(i.positionOS.xyz); o.positionCS=TransformWorldToHClip(o.positionWS); o.normalWS=TransformObjectToWorldNormal(i.normalOS); return o; }
            half4 frag(V i) : SV_Target
            {
                Light light=GetMainLight(TransformWorldToShadowCoord(i.positionWS));
                half n=dot(normalize(i.normalWS),light.direction);
                half band=n>.55?1.0:n>.05?.86:.66;
                band*=lerp(.78,1.0,light.shadowAttenuation);
                half3 shadow=lerp(half3(.83,.78,1),half3(1,1,1),band);
                return half4(_BaseColor.rgb*band*shadow,1);
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
    }
}
