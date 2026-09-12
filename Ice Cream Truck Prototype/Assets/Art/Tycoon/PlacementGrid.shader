Shader "Ice Cream/Placement Grid"
{
    Properties { _GridSize("Size", Vector)=(8,6,0,0) _CellSize("Cell size", Float)=.5 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
            float4 _GridSize; float _CellSize;
            CBUFFER_END
            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V vert(A i)
            {
                V o; o.positionCS=TransformObjectToHClip(i.positionOS.xyz); o.uv=i.uv; return o;
            }
            half4 frag(V i) : SV_Target
            {
                float2 cells=(i.uv-.5)*_GridSize.xy/_CellSize;
                float2 distance=abs(frac(cells+.5)-.5)/max(fwidth(cells),.0001);
                float lines=1-saturate(min(distance.x,distance.y)-.35);
                float2 edge=min(i.uv,1-i.uv)/max(fwidth(i.uv),.0001);
                float border=1-saturate(min(edge.x,edge.y)-1);
                return half4(1,1,1,max(lines*.65,border*.85));
            }
            ENDHLSL
        }
    }
}
