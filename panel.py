import bpy

class EZRENDER_PT_ez_render(bpy.types.Panel):
    bl_label = "Multi Render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EZ Render'
    bl_context = "objectmode"

        
    def draw(self, context):
        layout = self.layout.column()
        header, panel = layout.panel("ez_render_cameras")
        header.label(text="Cameras")
        if panel:
            for obj in [o for o in context.scene.objects if o.type == 'CAMERA']:
                row = panel.row()
                row.prop(obj, "ez_render_enabled", text="")
                row.prop(obj, "is_active", text=obj.name, toggle=1)
                row.prop(obj, "is_inactive", text="", icon="RESTRICT_RENDER_ON")
            
        # layout.separator()

        header, panel = layout.panel("ez_render_setup")
        header.label(text="Setup")
        if panel:
            row = panel.row()
            row.prop(context.scene, "ez_render_page_size", text="")
            row.prop(context.scene, "ez_render_page_dpi", text="DPI")
            row.prop(context.scene, "ez_render_page_orientation", text="")
            layout.operator("ez_render.set_resolution")
            layout.operator("ez_render.setup_cameras")
        
        # layout.separator()


        header, panel = layout.panel("ez_render_scale")
        header.label(text="Scale")
        if panel:
            def scale_button(layout, scale):
                op = layout.operator("ez_render.set_camera_scale", text = f"1:{scale}")
                op.scale = scale
                
            row = layout.row()
            scale_button(row, 1)
            scale_button(row, 2)
            scale_button(row, 5)
            
            row = layout.row()
            scale_button(row, 10)
            scale_button(row, 20)
            scale_button(row, 50)
            
            row = layout.row()
            scale_button(row, 100)
            scale_button(row, 200)
            scale_button(row, 500)
        
        # layout.separator()

        layout.operator("ez_render.render")
        
        
def register():
    bpy.utils.register_class(EZRENDER_PT_ez_render)

def unregister():
    bpy.utils.unregister_class(EZRENDER_PT_ez_render)
