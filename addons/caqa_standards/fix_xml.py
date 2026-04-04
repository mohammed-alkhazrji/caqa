import xml.etree.ElementTree as ET

def fix_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = root.find('data')
    if data is None:
        data = root

    # 1. Map standards to their subchapters
    standard_to_subchapter = {}
    for rec in data.findall("record[@model='caqa.standard']"):
        std_id = rec.get('id')
        subchapter_field = rec.find("field[@name='subchapter_id']")
        if subchapter_field is not None:
            standard_to_subchapter[std_id] = subchapter_field.get('ref')
            
    # Remove caqa.standard elements
    for rec in data.findall("record[@model='caqa.standard']"):
        data.remove(rec)

    # 2. Update indicators to point to subchapters instead of standards
    for rec in data.findall("record[@model='caqa.standard.indicator']"):
        std_field = rec.find("field[@name='standard_id']")
        if std_field is not None:
            std_ref = std_field.get('ref')
            if std_ref in standard_to_subchapter:
                std_field.set('name', 'subchapter_id')
                std_field.set('ref', standard_to_subchapter[std_ref])
            else:
                # If the standard_id refers to something else
                pass

    # 3. Calculate weights
    # We want Chapter = 10
    # Subchapter = 10 / num_subchapters
    # Indicator = Subchapter / num_indicators
    
    # Let's map children to parents
    chapter_children = {}      # chapter_id -> list of subchapter records
    subchapter_children = {}   # subchapter_id -> list of indicator records
    indicator_children = {}    # indicator_id -> list of checkpoint records
    
    for rec in data.findall("record[@model='caqa.standard.subchapter']"):
        c_id = rec.find("field[@name='chapter_id']").get('ref')
        chapter_children.setdefault(c_id, []).append(rec)
        
    for rec in data.findall("record[@model='caqa.standard.indicator']"):
        s_id = rec.find("field[@name='subchapter_id']").get('ref')
        subchapter_children.setdefault(s_id, []).append(rec)
        
    for rec in data.findall("record[@model='caqa.standard.checkpoint']"):
        i_id_field = rec.find("field[@name='indicator_id']")
        if i_id_field is not None:
            i_id = i_id_field.get('ref')
            indicator_children.setdefault(i_id, []).append(rec)

    # Set weights
    for chapter in data.findall("record[@model='caqa.standard.chapter']"):
        chapter_id = chapter.get('id')
        
        # Set chapter weight
        w_field = chapter.find("field[@name='weight']")
        if w_field is None:
            w_field = ET.SubElement(chapter, "field", name="weight")
        w_field.text = "10.0"
        
        # Process subchapters
        subchapters = chapter_children.get(chapter_id, [])
        if not subchapters: continue
        
        sub_weight = 10.0 / len(subchapters)
        for sub in subchapters:
            sub_id = sub.get('id')
            sw_field = sub.find("field[@name='weight']")
            if sw_field is None:
                sw_field = ET.SubElement(sub, "field", name="weight")
            sw_field.text = f"{sub_weight:.2f}"
            
            # Process indicators
            indicators = subchapter_children.get(sub_id, [])
            if not indicators: continue
            
            ind_weight = sub_weight / len(indicators)
            for ind in indicators:
                ind_id = ind.get('id')
                iw_field = ind.find("field[@name='weight']")
                if iw_field is None:
                    iw_field = ET.SubElement(ind, "field", name="weight")
                iw_field.text = f"{ind_weight:.2f}"
                
                # Checkpoints? Let's fix them too
                checkpoints = indicator_children.get(ind_id, [])
                if not checkpoints: continue
                
                # If points should sum to indicator weight, though usually checkpoints might just have a weight of 1 each and be max_score.
                # Actually, the user asked for empty weights to be filled out.
                # Standard checkpoints typically divide the indicator's weight. Let's do that for consistency unless we shouldn't.
                # Wait, checkpoints have weight and max_score. Let's set checkpoint weight = ind_weight / len(checkpoints)
                cp_weight = ind_weight / len(checkpoints)
                for cp in checkpoints:
                    cw_field = cp.find("field[@name='weight']")
                    if cw_field is None:
                        cw_field = ET.SubElement(cp, "field", name="weight")
                    cw_field.text = f"{cp_weight:.2f}"
                    
                    ms_field = cp.find("field[@name='max_score']")
                    if ms_field is None:
                        ms_field = ET.SubElement(cp, "field", name="max_score")
                    ms_field.text = f"{cp_weight:.2f}"

    # Write back
    # But first, how to make output look nice
    ET.indent(tree, space="    ", level=0)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

fix_xml('/home/alkhazrji/PycharmProjects/PythonProject8/odoo17/odoo/caqa_odoo18_complete/addons/caqa_standards/demo/caqa_data_from_pdf_with_generated_checkpoints.xml')
# Also probably good to fix the demo xml
fix_xml('/home/alkhazrji/PycharmProjects/PythonProject8/odoo17/odoo/caqa_odoo18_complete/addons/caqa_standards/demo/caqa_standards_demo.xml')
