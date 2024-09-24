bl_info = {
    "name": "EZ Render",
    "author": "matidfk",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Properties > EZ Render",
    "description": "Utilities for rendering multiple camera views such as plans and elevations",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}

import bpy
import os
import math
from . import panel

scale_magic_number = 0.42

class EZRENDER_OT_setup_cameras(bpy.types.Operator):
    """Docstring"""
    bl_idname = "ez_render.setup_cameras"
    bl_label = "Setup cameras"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    
    def execute(self, context):
        def create_cam(name, location, rotation):
            cam = bpy.data.cameras.new(name)
            cam.type = "ORTHO"
            obj = bpy.data.objects.new(name, cam)
            obj.location = location
            obj.rotation_euler = (math.radians(rotation[0]), math.radians(rotation[1]), math.radians(rotation[2]))
            obj.lock_rotation[0] = True
            obj.lock_rotation[1] = True
            obj.lock_rotation[2] = True
            bpy.context.scene.collection.objects.link(obj)
        
        create_cam("Front", (0,-20,0), (90, 0, 0))
        # create_cam("Back", (0,20,0), (90, 0, 180))
        create_cam("Left", (-20,0,0), (90, 0, -90))
        # create_cam("Right", (20,0,0), (90, 0, 90))
        create_cam("Top", (0,0,20), (0, 0, 0))
        
        create_cam("Isometric", (10,-10,10), (90 - 35.264, 0, 45))
        
        context.scene.camera = bpy.data.objects["Isometric"]

        # TODO RESOLUTION AND DPI
        context.scene.render.resolution_x = 4961
        context.scene.render.resolution_y = 3508
        
        return {"FINISHED"}
    
class EZRENDER_OT_set_camera_scale(bpy.types.Operator):
    """Docstring"""
    bl_idname = "ez_render.set_camera_scale"
    bl_label = "Set Camera Scale"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    scale: bpy.props.IntProperty(default=1)

    def execute(self, context):
        for obj in context.selected_objects:
            if obj is not None and obj.type == 'CAMERA':
                cam = obj.data
                if cam is not None:
                    cam.ortho_scale = self.scale * scale_magic_number
        
        return {"FINISHED"}


class EZRENDER_OT_set_resolution(bpy.types.Operator):
    """Docstring"""
    bl_idname = "ez_render.set_resolution"
    bl_label = "Set resolution"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)
        table = {
                "A2": [420, 594],
                "A3": [297, 420],
        }

        def inch(mm):
            return 0.0393701 * mm

        if context.scene.ez_render_page_orientation == "PORTRAIT":
            context.scene.render.resolution_x = round(inch(table[context.scene.ez_render_page_size][0]) * context.scene.ez_render_page_dpi)
            context.scene.render.resolution_y = round(inch(table[context.scene.ez_render_page_size][1]) * context.scene.ez_render_page_dpi)
        else:
            context.scene.render.resolution_x = round(inch(table[context.scene.ez_render_page_size][1]) * context.scene.ez_render_page_dpi)
            context.scene.render.resolution_y = round(inch(table[context.scene.ez_render_page_size][0]) * context.scene.ez_render_page_dpi)
        
        return {"FINISHED"}
    
        

# This is taken from some stack overflow post, could be changed but works for now
class EZRENDER_OT_render(bpy.types.Operator):
    bl_idname = "ez_render.render"
    bl_label = "EZ Render"

    _timer = None
    og_path = None

    def modal(self, context, event):
        if context.scene.ez_render_progress.is_finished():
            self.cancel(context)
            return {"FINISHED"}

        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.cancel(context)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        context.scene.ez_render_progress.reset()
        context.scene.render.filepath = self.og_path

    def execute(self, context):
        context.scene.ez_render_progress.reset()

        macro = get_macro(context)

        for obj in context.scene.objects:
            if obj.type == 'CAMERA' and obj.ez_render_enabled:
                pre = macro.define("RENDER_OT_ez_render_pre")
                pre.properties.camera_name = obj.name
                pre.properties.path = context.scene.render.filepath

                render = macro.define("RENDER_OT_render")
                render.properties.write_still = True

                post = macro.define("RENDER_OT_ez_render_post")
            macro.steps += 1

        self.og_path = context.scene.render.filepath

        context.scene.ez_render_progress.total = macro.steps

        bpy.ops.render.ez_render_macro("INVOKE_DEFAULT")

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}


def get_macro(context):
    # redefine the class to clear any previous steps assigned to the macro
    class RENDER_OT_ez_render_macro(bpy.types.Macro):
        bl_idname = "render.ez_render_macro"
        bl_label = "Render Macro"
        bl_options = {"INTERNAL", "MACRO"}

        steps = 0

    # unregister any previous macro
    if hasattr(bpy.types, "RENDER_OT_ez_render_macro"):
        bpy.utils.unregister_class(bpy.types.RENDER_OT_ez_render_macro)

    bpy.utils.register_class(RENDER_OT_ez_render_macro)
    return RENDER_OT_ez_render_macro


class RENDER_OT_ez_render_pre(bpy.types.Operator):
    bl_idname = "render.ez_render_pre"
    bl_label = "Render pre"
    bl_options = {'INTERNAL'}

    path: bpy.props.StringProperty()
    camera_name: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.camera = context.scene.objects[self.camera_name]
        context.scene.render.filepath = os.path.join(self.path, self.camera_name) + "." + context.scene.render.image_settings.file_format.lower()
        print(f"PRE {self.camera_name}")
        return {"FINISHED"}

class RENDER_OT_ez_render_post(bpy.types.Operator):
    bl_idname = "render.ez_render_post"
    bl_label = "Render post"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        res = (100.0/2.54) * context.scene.ez_render_page_dpi
        bpy.ops.image.open(filepath=context.scene.render.filepath)
        imgname = context.scene.camera.name + "." + context.scene.render.image_settings.file_format.lower()

        img = bpy.data.images[imgname]
        img.resolution = (res, res)
        img.save()
        return {"FINISHED"}



class EzRenderProgress(bpy.types.PropertyGroup):
    progress: bpy.props.IntProperty(default=0)
    total: bpy.props.IntProperty(default=0)

    def increment(self):
        self.progress += 1

    def get_progress_fac(self):
        if self.total == 0:
            return 0.0
        else:
            return self.progress / self.total

    def get_progress_string(self):
        return f'{self.progress} / {self.total}'

    def is_finished(self):
        return self.progress == self.total

    def reset(self):
        self.progress = 0
        self.total = 0


classes = (
    EZRENDER_OT_render,
    EZRENDER_OT_setup_cameras,
    EZRENDER_OT_set_camera_scale,
    EZRENDER_OT_set_resolution,
    RENDER_OT_ez_render_pre,
    RENDER_OT_ez_render_post,
    EzRenderProgress,
)

def get_is_active(self):
    return bpy.context.scene.camera == self.original
    
def set_is_active(self, value):
    old = bpy.context.scene.camera
    if value and self.original != old:
        bpy.context.scene.camera = self.original
        old.update_tag()

def get_is_inactive(self):
    return not bpy.context.scene.camera == self.original

def set_dummy(self, value):
    return
    
def register():
    bpy.types.Object.is_active = bpy.props.BoolProperty(name="Is Active", get=get_is_active, set=set_is_active)
    bpy.types.Object.is_inactive = bpy.props.BoolProperty(name="Is Inactive", get=get_is_inactive, set=set_dummy)
    bpy.types.Object.ez_render_enabled = bpy.props.BoolProperty(name="Enabled")

    bpy.types.Scene.ez_render_page_size = bpy.props.EnumProperty(items=[("A2", "A2", "A2"),
                                                                        ("A3", "A3", "A3")])

    bpy.types.Scene.ez_render_page_dpi = bpy.props.IntProperty(default=300)
    bpy.types.Scene.ez_render_page_orientation = bpy.props.EnumProperty(items=[("PORTRAIT", "Portrait", "Vertical"),
                                                                               ("LANDSCAPE", "Landscape", "Horizontal")])

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ez_render_progress = bpy.props.PointerProperty(type=EzRenderProgress)


    panel.register()
    
 
def unregister():
    panel.unregister()
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
if __name__ == "__main__":
    register()
