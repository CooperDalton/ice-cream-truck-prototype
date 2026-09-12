Shader "Ice Cream/Placement Ghost"
{
    Properties { _BaseColor("Tint", Color) = (1,1,1,.48) }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent+10" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            CBUFFER_END
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct V { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; };
            V vert(A i)
            {
                V o; o.positionCS=TransformObjectToHClip(i.positionOS.xyz); o.normalWS=TransformObjectToWorldNormal(i.normalOS); return o;
            }
            half4 frag(V i) : SV_Target
            {
                half shade=.65+.35*saturate(dot(normalize(i.normalWS),normalize(float3(.4,1,-.3))));
                return half4(_BaseColor.rgb*shade,_BaseColor.a);
            }
            ENDHLSL
        }
    }
}
