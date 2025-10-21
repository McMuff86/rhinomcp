#!/usr/bin/env python3

import sys
sys.path.insert(0, 'rhino_mcp_server/src')

from rhinomcp.tools.create_layer import create_layer
from rhinomcp.tools.create_material import create_material
from rhinomcp.tools.assign_material_to_layer import assign_material_to_layer
from rhinomcp.tools.get_or_set_current_layer import get_or_set_current_layer
from rhinomcp.tools.create_object import create_object
from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code
from rhinomcp.tools.log_thought import log_thought
from mcp.server.fastmcp import Context

def complete_cleanup_and_rebuild():
    ctx = Context()

    print("=== COMPLETE PBR SETUP FROM SCRATCH ===")
    print("Debug Mode: ENABLED")
    print("AI Thoughts: ENABLED")
    print()

    # Step 1: Log start
    log_thought(ctx, 'Starte vollständiges Layer-basiertes PBR Setup von Grund auf')

    # Step 2: Create PBR layers
    print("Creating PBR Material Layers...")
    gold_layer = create_layer(ctx, name='Gold_Material_Layer', color=[255, 215, 0])
    silver_layer = create_layer(ctx, name='Silver_Material_Layer', color=[192, 192, 192])
    platinum_layer = create_layer(ctx, name='Platinum_Material_Layer', color=[229, 228, 226])

    print(f"Gold Layer: {gold_layer}")
    print(f"Silver Layer: {silver_layer}")
    print(f"Platinum Layer: {platinum_layer}")
    print()

    # Step 3: Create PBR materials
    log_thought(ctx, 'Erstelle echte PBR Materialien für die Layer')
    print("Creating PBR Materials...")

    gold_material = create_material(ctx, name='Gold_PBR', color=[255, 215, 0], material_type='pbr', metallic=0.95, roughness=0.05)
    silver_material = create_material(ctx, name='Silver_PBR', color=[192, 192, 192], material_type='pbr', metallic=0.90, roughness=0.08)
    platinum_material = create_material(ctx, name='Platinum_PBR', color=[229, 228, 226], material_type='pbr', metallic=0.92, roughness=0.06)

    print(f"Gold Material: {gold_material}")
    print(f"Silver Material: {silver_material}")
    print(f"Platinum Material: {platinum_material}")
    print()

    # Step 4: Assign materials to layers
    log_thought(ctx, 'Weise PBR Materialien den Layern zu')
    print("Assigning Materials to Layers...")

    assign1 = assign_material_to_layer(ctx, layer_name='Gold_Material_Layer', material_id='0')
    assign2 = assign_material_to_layer(ctx, layer_name='Silver_Material_Layer', material_id='1')
    assign3 = assign_material_to_layer(ctx, layer_name='Platinum_Material_Layer', material_id='2')

    print(f"Gold Assignment: {assign1}")
    print(f"Silver Assignment: {assign2}")
    print(f"Platinum Assignment: {assign3}")
    print()

    # Step 5: Create spheres on layers
    log_thought(ctx, 'Erstelle Kugeln auf den PBR Material Layern')
    print("Creating Spheres on PBR Layers...")

    # Gold sphere
    get_or_set_current_layer(ctx, name='Gold_Material_Layer')
    gold_sphere = create_object(ctx, type='SPHERE', name='Gold_Sphere', params={'radius': 1.0}, translation=[-3, 0, 0])
    print(f"Gold Sphere: {gold_sphere}")

    # Silver sphere
    get_or_set_current_layer(ctx, name='Silver_Material_Layer')
    silver_sphere = create_object(ctx, type='SPHERE', name='Silver_Sphere', params={'radius': 1.0}, translation=[0, 0, 0])
    print(f"Silver Sphere: {silver_sphere}")

    # Platinum sphere
    get_or_set_current_layer(ctx, name='Platinum_Material_Layer')
    platinum_sphere = create_object(ctx, type='SPHERE', name='Platinum_Sphere', params={'radius': 1.0}, translation=[3, 0, 0])
    print(f"Platinum Sphere: {platinum_sphere}")

    print()
    print("=== PBR SETUP COMPLETED SUCCESSFULLY ===")
    print("Gold_Sphere (-3, 0, 0) on Gold_Material_Layer")
    print("Silver_Sphere (0, 0, 0) on Silver_Material_Layer")
    print("Platinum_Sphere (3, 0, 0) on Platinum_Material_Layer")
    print()
    print("In Rhino: Use Rendered View to see realistic PBR reflections!")
    print("Objects automatically inherit PBR materials from their layers!")

    # Final log
    log_thought(ctx, 'Layer-basiertes PBR Setup vollständig abgeschlossen - Gold, Silver, Platinum Kugeln mit automatischem Material-Erbe')

if __name__ == "__main__":
    complete_cleanup_and_rebuild()
