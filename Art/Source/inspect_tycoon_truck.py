import bpy
col=bpy.data.collections['Toon / Ice cream truck']
for obj in col.objects:
    if obj.type=='EMPTY':print(obj.name,'PARENT',obj.parent.name if obj.parent else '')
