import json
from io import BytesIO

import geopandas
from viktor import (
    ViktorController,
    Color,GeoPolygonField,
    GeoPointField,
    GeoPolylineField,
    MapLegend
)
from viktor.parametrization import (
    ViktorParametrization,
    DynamicArray,
    FileField,
    ColorField,
    Text,
    Section,
    Tab
)
from viktor.views import (
    GeoJSONResult,
    GeoJSONView,
    MapLabel
)

j_colors = {'blues': {0: '#231EDC', 1: '#0A7DFF', 2: '#5AE6FF', 3: '#001E55'},
            'purples': {0: '#6F006E', 1: '#A800A8', 2: '#D7A5F5', 3: '#460F32'},
            'red': {0: '#D72850', 1: '#FF465F', 2:'#FF9191', 3:'#690A28'},
            'yellows': {0: '#FFA014', 1: '#FFB41E', 2:'#FFDC78', 3: '#C05C27'},
            'greens': {0: '#007D55', 1: '#0AD287', 2:'#78FAC8', 3: '#003C2D'}}


class Parametrization(ViktorParametrization):

    welcome_tab = Tab('ReadMe')
    welcome_tab.welcome_text = Text("""# Welcome to the Shawfair Connections Data Viewer.
With this app you can veiw the project data, draw on the map, and also upload your own shapefiles.""")
    

    add_tab = Tab('Add to Map')
    add_tab.draw_section = Section("Draw a polygon, line or points: ")

    add_tab.draw_section.polyline_da = DynamicArray('Add Lines:')
    add_tab.draw_section.polyline_da.polyline = GeoPolylineField('Line')

    add_tab.draw_section.polygon_da = DynamicArray('Add Polygons:')
    add_tab.draw_section.polygon_da.polygon = GeoPolygonField('Polygon')

    add_tab.draw_section.point_da = DynamicArray('Add Points:')
    add_tab.draw_section.point_da.point = GeoPointField('Point')


    add_tab.shp_upload_section = Section("Upload your own Shapefile")
    add_tab.shp_upload_section.dynamic_array = DynamicArray('List of project files')
    add_tab.shp_upload_section.dynamic_array.shp_file = FileField('Upload Shapefile', file_types=['.zip'])
    add_tab.shp_upload_section.dynamic_array.color = ColorField('Colour of objects', default=Color.viktor_blue())


    legend_tab = Tab('Legend')
    legend_tab.legend_text = Text("""Content to Follow""")


class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=30)

    @GeoJSONView('Map', duration_guess=1)
    def get_geojson_view(self, params, **kwargs):
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }


        initial_routes_colors = [j_colors['blues'][1], j_colors['greens'][1], j_colors['purples'][1], j_colors['red'][1], j_colors['yellows'][1]]
        initial_routes_legend = []
        initial_routes_gdf = geopandas.read_file('shapefiles/initial routes/initial_routes.shp')
        initial_routes_gdf = initial_routes_gdf.to_crs('EPSG:4326')
        _geojson = json.loads(initial_routes_gdf.to_json())
        for fdx, feature in enumerate(_geojson['features']):
            feature['properties']['description'] = '**Description**  \n' + '  \n'.join([f"**{k}:** {v}" for k, v in feature['properties'].items()])
            feature['properties']['marker-color'] = '#000000'
            feature['properties']['stroke'] = initial_routes_colors[fdx]
            feature['properties']['marker-size'] = 'medium'

            initial_routes_legend.append((Color.from_hex(initial_routes_colors[fdx]), f'{feature['properties']['Route Nb']}: {feature['properties']['Name']}'))
        geojson['features'].extend(_geojson['features'])

        council_boundaries_gdf = geopandas.read_file('shapefiles/council boundaries/council_boundaries.shp')
        council_boundaries_gdf = council_boundaries_gdf.to_crs('EPSG:4326')
        _geojson = json.loads(council_boundaries_gdf.to_json())
        for fdx, feature in enumerate(_geojson['features']):
            feature['properties']['description'] = f'**Council Area**  \n {feature['properties']['name']}'
            feature['properties']['marker-color'] = '#ffffff'
            feature['properties']['stroke'] = '#000000'
            feature['properties']['marker-size'] = 'large'
            feature['properties']['fill-opacity'] = 0.1
        
        geojson['features'].extend(_geojson['features'])

        ncn_gdf = geopandas.read_file('shapefiles/Scotland National Cycle Network/Scotland_NCN.shp')
        ncn_gdf = ncn_gdf.to_crs('EPSG:4326')
        _geojson = json.loads(ncn_gdf.to_json())
        for fdx, feature in enumerate(_geojson['features']):
            feature['properties']['description'] = '**Description**  \n' + '  \n'.join([f"**{k}:** {v}" for k, v in feature['properties'].items()])
            feature['properties']['marker-color'] = '#000000'
            feature['properties']['stroke'] = j_colors['greens'][3]
            feature['properties']['marker-size'] = 'small'

        geojson['features'].extend(_geojson['features'])
        ncn_legend = [(Color.from_hex(j_colors['greens'][3]), 'NCN in Scotland')]
        
        for row in params.add_tab.shp_upload_section.dynamic_array:
            if not row.get('shp_file'):
                continue
            _gdf = geopandas.read_file(BytesIO(row.shp_file.file.getvalue_binary()))
            _gdf = _gdf.to_crs('EPSG:4326')
            _geojson = json.loads(_gdf.to_json())
            for feature in _geojson['features']:
                feature['properties']['description'] = '**Description**  \n' + '  \n'.join([f"**{k}:** {v}" for k, v in feature['properties'].items()])
                feature['properties']['marker-color'] = row.color.hex
                feature['properties']['stroke'] = row.color.hex
                feature['properties']['fill'] = row.color.hex
                feature['properties']['marker-size'] = 'small'
            geojson['features'].extend(_geojson['features'])

        
        # visualise point features
        _point_geojson_features = []
        if len(params.add_tab.draw_section.point_da) > 0:
            for p in params.add_tab.draw_section.point_da:
                if p.point:
                    print(p.point)
                    print(p.point.lat)
                    feature = [{'type': 'Feature',
                            'properties': {'marker-color': '#000000'},
                            'geometry':{
                                'type': 'Point',
                                'coordinates': [p.point.lon, p.point.lat]
                            }
                            }]

                    _point_geojson_features.extend(feature)
        geojson['features'].extend(_point_geojson_features)

        # TODO visualise line features

        # TODO visualise polygon features


        legend = MapLegend(initial_routes_legend + ncn_legend)

        return GeoJSONResult(geojson, legend=legend)