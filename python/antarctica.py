import numpy as np
import trimesh
import fiona
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from shapely.ops import unary_union, polygonize

# ----------------------------
# USER PARAMS
coast_shp = "../data/natural_earth/ne_110m_coastline.shp"

R = 76.2          # mm: sphere radius (6" diameter => 76.2mm radius)
k = 1.05          # raise factor: outer radius = R*k

out_stl = "antarctica_raised_patch.stl"
# ----------------------------

def boundary_edges_from_faces(F: np.ndarray) -> np.ndarray:
    """
    Return boundary edges (m,2) from triangular faces F (n,3).
    Boundary edges are those that appear exactly once across all triangles.
    """
    F = np.asarray(F, dtype=np.int64)
    if F.ndim != 2 or F.shape[1] != 3:
        raise ValueError("F must be an (n,3) array of triangle indices")

    # All directed edges from faces
    e01 = F[:, [0, 1]]
    e12 = F[:, [1, 2]]
    e20 = F[:, [2, 0]]
    E = np.vstack([e01, e12, e20])

    # Make edges undirected by sorting endpoints
    E_sorted = np.sort(E, axis=1)

    # Count occurrences of each undirected edge
    # np.unique with return_counts works reliably across versions
    uniq, counts = np.unique(E_sorted, axis=0, return_counts=True)

    # Boundary edges appear exactly once
    boundary = uniq[counts == 1]
    return boundary

def d2r(d): return d * np.pi / 180.0
def r2d(r): return r * 180.0 / np.pi

def wrap_lon(lon_deg):
    return (lon_deg + 180.0) % 360.0 - 180.0

def stereographic_south_pole_fwd(lon_deg, lat_deg):
    lon = d2r(wrap_lon(lon_deg))
    lat = d2r(lat_deg)
    chi = np.pi/2 + lat            # lat=-90 => chi=0
    r = 2.0 * np.tan(chi / 2.0)    # well-behaved near South Pole
    x = r * np.sin(lon)
    y = r * np.cos(lon)
    return x, y

def stereographic_south_pole_inv(x, y):
    r = np.sqrt(x*x + y*y)
    chi = 2.0 * np.arctan(r / 2.0)
    lon = np.arctan2(x, y)
    lat = chi - np.pi/2
    return r2d(lon), r2d(lat)

def ll_to_xyz(lon_deg, lat_deg, radius):
    lon = d2r(lon_deg)
    lat = d2r(lat_deg)
    return np.array([
        radius * np.cos(lat) * np.cos(lon),
        radius * np.cos(lat) * np.sin(lon),
        radius * np.sin(lat)
    ], dtype=float)

def polygon_ll_to_polygon_xy(poly_ll: Polygon) -> Polygon:
    lonlat = np.array(poly_ll.exterior.coords, dtype=float)
    xy = np.array([stereographic_south_pole_fwd(lon, lat) for lon, lat in lonlat], dtype=float)
    return Polygon(xy)

# --- REQUIRED: inverse projection and ll_to_xyz must exist in your file ---
# stereographic_south_pole_inv(x, y) -> (lon_deg, lat_deg)
# ll_to_xyz(lon_deg, lat_deg, radius) -> np.array([x,y,z])

def build_raised_patch_from_polygon_ll(poly_ll: Polygon, R: float, k: float) -> trimesh.Trimesh:
    poly_xy = polygon_ll_to_polygon_xy(poly_ll)

    poly_xy = poly_xy.buffer(0)
    if poly_xy.is_empty:
        raise RuntimeError("Projected polygon is empty after buffer(0).")

    tri = trimesh.creation.triangulate_polygon(poly_xy)

    # Normalize triangulation output to (V2, F)
    if isinstance(tri, tuple):
        V2, F = tri
        V2 = np.asarray(V2, dtype=float)
        F  = np.asarray(F, dtype=int)
    else:
        V2 = np.asarray(tri.vertices[:, :2], dtype=float)
        F  = np.asarray(tri.faces, dtype=int)

    if len(V2) == 0 or len(F) == 0:
        raise RuntimeError("Triangulation produced empty output.")

    # Compute boundary edges ourselves (no trimesh helper needed)
    edges = boundary_edges_from_faces(F)

    # Inverse project vertices back to lon/lat
    lonlat = np.array([stereographic_south_pole_inv(x, y) for x, y in V2], dtype=float)

    # Inner/outer vertices
    Vin  = np.array([ll_to_xyz(lon, lat, R) for lon, lat in lonlat], dtype=float)
    Vout = np.array([ll_to_xyz(lon, lat, R * k) for lon, lat in lonlat], dtype=float)

    n = len(Vin)
    V = np.vstack([Vin, Vout])

    faces = []

    # Outer surface
    for a, b, c in F:
        faces.append([int(a + n), int(b + n), int(c + n)])

    # Inner surface (reverse winding)
    for a, b, c in F:
        faces.append([int(c), int(b), int(a)])

    # Sidewalls along boundary
    for i, j in edges:
        i = int(i); j = int(j)
        faces.append([i, j, j + n])
        faces.append([i, j + n, i + n])

    mesh = trimesh.Trimesh(vertices=V, faces=np.asarray(faces, dtype=int), process=True)
    mesh.remove_duplicate_faces()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh

def load_coastline_lines(shp_path):
    geoms = []
    with fiona.open(shp_path) as src:
        for rec in src:
            g = shape(rec["geometry"])
            if not g.is_empty:
                geoms.append(g)
    if not geoms:
        raise RuntimeError("No geometries loaded from coastline shapefile.")
    return geoms

def polygonize_landmasses_from_coastlines(lines):
    # Merge all coastline segments into one network
    merged = unary_union(lines)
    # Polygonize creates polygons on either side of closed linework
    polys = list(polygonize(merged))
    if not polys:
        raise RuntimeError("polygonize() returned no polygons. Coastline linework may be incomplete.")
    return polys

def pick_antarctica_polygon(polys):
    # Choose a point that is definitely on Antarctica (lon=0, lat=-80 is safe)
    p = Point(0.0, -80.0)

    # Keep only polygons that contain that point
    candidates = [poly for poly in polys if poly.contains(p)]
    if not candidates:
        # fallback: sometimes the point falls on boundary; try nearby points
        for lon, lat in [(0, -75), (30, -80), (-60, -80), (120, -80)]:
            p2 = Point(float(lon), float(lat))
            candidates = [poly for poly in polys if poly.contains(p2)]
            if candidates:
                break

    if not candidates:
        raise RuntimeError("Could not find an Antarctica polygon containing test points. Dateline/geometry issue likely.")

    # If multiple, pick the largest by area (in degrees^2, but works for comparison)
    ant = max(candidates, key=lambda poly: poly.area)
    return ant

def main():
    lines = load_coastline_lines(coast_shp)
    polys = polygonize_landmasses_from_coastlines(lines)

    ant = pick_antarctica_polygon(polys)

    # Clean geometry in lon/lat space
    ant = ant.buffer(0)
    if ant.is_empty:
        raise RuntimeError("Antarctica polygon invalid after buffer(0).")

    # If MultiPolygon appears, pick the largest piece
    if isinstance(ant, MultiPolygon):
        ant = max(list(ant.geoms), key=lambda p: p.area)

    mesh = build_raised_patch_from_polygon_ll(ant, R=R, k=k)

    print("Watertight:", mesh.is_watertight)
    print("Faces:", len(mesh.faces), "Verts:", len(mesh.vertices))
    mesh.export(out_stl)
    print("Wrote:", out_stl)

if __name__ == "__main__":
    main()
