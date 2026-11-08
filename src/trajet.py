"""Station conseillée pour prendre ou déposer un vélo près d'un point (issue #26)."""
import math

RAYON_TERRE_M = 6_371_000
COLONNE_BESOIN = {"velo": "numbikesavailable", "borne": "numdocksavailable"}


def distance_m(lat1, lon1, lat2, lon2):
    """Calcule la distance à vol d'oiseau entre deux points GPS (formule de haversine).

    Reçoit : latitude et longitude des deux points, en degrés.
    Renvoie : la distance en mètres (nombre décimal).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * RAYON_TERRE_M * math.asin(math.sqrt(a))


def station_conseillee(df, lat, lon, besoin):
    """Trouve la meilleure station autour d'un point.

    Reçoit : le tableau nettoyé, un point (lat, lon) et besoin = "velo" (pour prendre
    un vélo) ou "borne" (pour en déposer un).
    Renvoie : dict name, distance_m (mètres, entier), nombre (vélos ou bornes libres),
    mechanical, ebike (vélos mécaniques / électriques), lat, lon ;
    ou None si aucune station ne convient.
    Règles : stations en service seulement, avec au moins 1 vélo (ou 1 borne libre) ;
    la plus proche ; à distance égale, celle qui a le plus de vélos (ou de bornes).
    Lève ValueError si besoin n'est ni "velo" ni "borne".
    """
    if besoin not in COLONNE_BESOIN:
        raise ValueError(f'besoin doit valoir "velo" ou "borne", pas {besoin!r}')
    colonne = COLONNE_BESOIN[besoin]

    candidates = df[df["en_service"] & (df[colonne] >= 1)].copy()
    if candidates.empty:
        return None
    # Arrondi au mètre : deux stations « à la même distance » sont départagées par le nombre
    candidates["distance_m"] = [
        round(distance_m(lat, lon, lat_station, lon_station))
        for lat_station, lon_station in zip(candidates["lat"], candidates["lon"])
    ]
    meilleure = candidates.sort_values(["distance_m", colonne], ascending=[True, False]).iloc[0]
    return {
        "name": meilleure["name"],
        "distance_m": int(meilleure["distance_m"]),
        "nombre": int(meilleure[colonne]),
        "mechanical": int(meilleure["mechanical"]),
        "ebike": int(meilleure["ebike"]),
        "lat": float(meilleure["lat"]),
        "lon": float(meilleure["lon"]),
    }


def stations_proches(df, lat, lon, rayon_m=500):
    """Liste les stations autour d'un point, de la plus proche à la plus lointaine.

    Reçoit : le tableau nettoyé, un point (lat, lon) et un rayon en mètres.
    Renvoie : les lignes du tableau situées dans le rayon (hors service comprises),
    avec une colonne distance_m (mètres, entier) en plus, triées par distance.
    """
    proches = df.copy()
    proches["distance_m"] = [
        round(distance_m(lat, lon, lat_station, lon_station))
        for lat_station, lon_station in zip(proches["lat"], proches["lon"])
    ]
    return proches[proches["distance_m"] <= rayon_m].sort_values("distance_m")
