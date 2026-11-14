from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from astroquery.jplhorizons import Horizons

# API uygulamasını başlat
app = FastAPI(
    title="Lunar Landing Site API",
    description="NASA JPL Horizons'tan Ay Güney Kutbu için Güneş ve Dünya konumlarını çeker."
)

# CORS Ayarları: Önyüzün (Frontend) farklı bir porttan istek atmasına izin verir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşamasında herkese açık, canlıda spesifik domain girilir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/positions")
async def get_positions(
    lat: float = Query(-89.9, description="Ay üzerindeki Enlem (Güney Kutbu için negatif)"),
    lon: float = Query(0.0, description="Ay üzerindeki Boylam"),
    start_date: str = Query("2026-10-01", description="Başlangıç Tarihi (YYYY-MM-DD)"),
    stop_date: str = Query("2026-10-05", description="Bitiş Tarihi (YYYY-MM-DD)"),
    step: str = Query("1h", description="Zaman adımı (örn: '1h' saatlik, '1d' günlük)")
):
    lunar_location = {
        'lon': lon,
        'lat': lat,
        'elevation': 0.0,
        'body': '301'
    }
    
    epochs = {'start': start_date, 'stop': stop_date, 'step': step}

    try:
        # JPL Horizons API'den verileri çek
        sun_query = Horizons(id='10', location=lunar_location, epochs=epochs)
        sun_data = sun_query.ephemerides(quantities='4')

        earth_query = Horizons(id='399', location=lunar_location, epochs=epochs)
        earth_data = earth_query.ephemerides(quantities='4')

        # Verileri önyüzün (frontend) seveceği JSON formatına çevir
        results = []
        for i in range(len(sun_data)):
            results.append({
                "datetime": str(sun_data['datetime_str'][i]),
                "sun": {
                    "azimuth": float(sun_data['AZ'][i]),
                    "elevation": float(sun_data['EL'][i]),
                    "is_visible": bool(sun_data['EL'][i] > 0) # Ufkun üzerindeyse True
                },
                "earth": {
                    "azimuth": float(earth_data['AZ'][i]),
                    "elevation": float(earth_data['EL'][i]),
                    "is_visible": bool(earth_data['EL'][i] > 0) # Ufkun üzerindeyse True
                }
            })
            
        return {"status": "success", "data": results}

    except Exception as e:
        # Hata durumunda mantıklı bir hata mesajı dön
        raise HTTPException(status_code=500, detail=f"JPL Horizons API Hatası: {str(e)}")