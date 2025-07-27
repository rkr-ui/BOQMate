import ezdxf
import os
from typing import Dict, Any, List
import json

class CADProcessor:
    def __init__(self):
        self.supported_formats = ['.dwg', '.dxf', '.rvt', '.rfa', '.dgn', '.skp']
    
    def process_dxf_file(self, file_content: bytes, filename: str) -> str:
        """Process DXF files using ezdxf"""
        try:
            # Create a temporary file to process with ezdxf
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Read DXF file
            doc = ezdxf.read(temp_file_path)
            msp = doc.modelspace()
            
            # Extract information from DXF
            entities_info = []
            
            for entity in msp:
                entity_type = entity.dxftype()
                entity_info = {
                    'type': entity_type,
                    'layer': getattr(entity, 'dxf', {}).get('layer', 'Unknown'),
                }
                
                # Extract specific information based on entity type
                if entity_type == 'LINE':
                    entity_info.update({
                        'start': (entity.dxf.start.x, entity.dxf.start.y),
                        'end': (entity.dxf.end.x, entity.dxf.end.y),
                        'length': entity.dxf.start.distance(entity.dxf.end)
                    })
                elif entity_type == 'CIRCLE':
                    entity_info.update({
                        'center': (entity.dxf.center.x, entity.dxf.center.y),
                        'radius': entity.dxf.radius,
                        'area': 3.14159 * entity.dxf.radius ** 2
                    })
                elif entity_type == 'POLYLINE':
                    points = list(entity.get_points())
                    entity_info.update({
                        'points_count': len(points),
                        'points': [(p[0], p[1]) for p in points]
                    })
                elif entity_type == 'TEXT':
                    entity_info.update({
                        'text': entity.dxf.text,
                        'position': (entity.dxf.insert.x, entity.dxf.insert.y)
                    })
                
                entities_info.append(entity_info)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Create a summary of the CAD file
            summary = {
                'filename': filename,
                'format': 'DXF',
                'total_entities': len(entities_info),
                'layers': list(set(e['layer'] for e in entities_info)),
                'entity_types': list(set(e['type'] for e in entities_info)),
                'entities': entities_info[:50]  # Limit to first 50 entities for analysis
            }
            
            return json.dumps(summary, indent=2)
            
        except Exception as e:
            return f"Error processing DXF file: {str(e)}"
    
    def process_cad_file(self, file_content: bytes, filename: str) -> str:
        """Process various CAD file formats"""
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension == 'dxf':
            return self.process_dxf_file(file_content, filename)
        elif file_extension == 'dwg':
            # DWG files require additional libraries like ODA File Converter
            # For now, return a generic analysis
            return f"""
CAD File Analysis:
- Filename: {filename}
- Format: DWG (AutoCAD Drawing)
- Note: DWG files require specialized processing tools
- Recommendation: Convert to DXF format for better analysis
            """
        elif file_extension in ['rvt', 'rfa']:
            return f"""
CAD File Analysis:
- Filename: {filename}
- Format: {file_extension.upper()} (Revit File)
- Note: Revit files require Autodesk Revit or specialized tools
- Recommendation: Export to IFC or DXF format for analysis
            """
        elif file_extension == 'dgn':
            return f"""
CAD File Analysis:
- Filename: {filename}
- Format: DGN (MicroStation Design File)
- Note: DGN files require Bentley MicroStation or specialized tools
- Recommendation: Convert to DXF format for analysis
            """
        elif file_extension == 'skp':
            return f"""
CAD File Analysis:
- Filename: {filename}
- Format: SKP (SketchUp Model)
- Note: SketchUp files require SketchUp or specialized tools
- Recommendation: Export to DXF or IFC format for analysis
            """
        else:
            return f"""
CAD File Analysis:
- Filename: {filename}
- Format: {file_extension.upper()}
- Note: Unsupported CAD format
- Recommendation: Convert to DXF format for analysis
            """
    
    def extract_quantities_from_cad(self, cad_analysis: str) -> Dict[str, Any]:
        """Extract quantities from CAD analysis for BOQ generation"""
        try:
            analysis_data = json.loads(cad_analysis)
            
            quantities = {
                'total_entities': analysis_data.get('total_entities', 0),
                'layers_count': len(analysis_data.get('layers', [])),
                'entity_types': analysis_data.get('entity_types', []),
                'estimated_area': 0,
                'estimated_length': 0,
                'text_elements': 0
            }
            
            # Calculate estimated quantities from entities
            for entity in analysis_data.get('entities', []):
                if entity.get('type') == 'CIRCLE':
                    quantities['estimated_area'] += entity.get('area', 0)
                elif entity.get('type') == 'LINE':
                    quantities['estimated_length'] += entity.get('length', 0)
                elif entity.get('type') == 'TEXT':
                    quantities['text_elements'] += 1
            
            return quantities
            
        except json.JSONDecodeError:
            # If not JSON, return basic analysis
            return {
                'total_entities': 0,
                'layers_count': 0,
                'entity_types': [],
                'estimated_area': 0,
                'estimated_length': 0,
                'text_elements': 0,
                'note': 'CAD file analysis completed'
            } 